
### --- definition coroutines --- ###
{% include 'nats_coroutines.py' %}
### --- end coroutines --- ###

def create_target_interaction_dag(dag_id, config, identifier):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder subdag for interacting with targets')

    with dag as interaction_dag:

        dump_config = BashOperator(
            task_id='print_config',
            bash_command='echo ${config}',
            env={"config": str(config)},
            dag=interaction_dag,
        )

        @dag.task(task_id="pull_optimization_step")
        def run_pull_optimization():
            task_logger.debug("Entering")

            msg = asyncio.run(receive_msg_via_nats(subject=f'effectuation_{identifier}'))
            settings = json.loads(msg).get('settings')

            task_logger.debug(f"Settings: f{settings}")

            return settings

        pull_step = run_pull_optimization()

        @dag.task(task_id="push_optimization_step")
        def run_push_optimization(ti=None):
            task_logger.debug("Entering")

            metric_value = ti.xcom_pull(task_ids="recon_step")

            task_logger.debug(f"Metric : f{metric_value}")

            metric_data = dict(metric=metric_value)
            msg = asyncio.run(send_msg_via_nats(subject=f'recon_{identifier}', data_dict=metric_data))

            task_logger.debug("Done")

            return msg

        push_step = run_push_optimization()

        @dag.task(task_id="recon_step")
        def run_reconnaissance():
            task_logger.debug("Entering")
            prom_conn = PrometheusConnect(url ="http://godon_prometheus_1:9090", disable_ssl=True)

            start_time = parse_datetime("2m")
            end_time = parse_datetime("now")
            chunk_size = timedelta(minutes=1)

            metric_data = dict()
            for query in config.get('recon').get('prometheus'):
                query_name = query.get('name')
                query_string = query.get('query')
                query_result = prom_conn.custom_query(query_string)
                metric_value = query_result[0]
                metric_data[query_name] = metric_value.get('value')[1]

            task_logger.debug("Done")

            return metric_data

        recon_step = run_reconnaissance()

        _ssh_hook = SSHHook(
            remote_host=config.get('effectuation').get('target'),
            username=config.get('effectuation').get('user'),
            key_file=config.get('effectuation').get('key_file'),
            timeout=30,
            keepalive_interval=10
        )

{% raw %}
        effectuation_step = SSHOperator(
            ssh_hook=_ssh_hook,
            task_id='effectuation',
            timeout=30,
            command="""
                    {{ ti.xcom_pull(task_ids='pull_optimization_step') }}
                    """,
            dag=interaction_dag,
        )
{% endraw %}

        @dag.task(task_id="run_iter_count_step")
        def run_iter_count(ti=None):
            last_iteration =  ti.xcom_pull(task_ids="run_iter_count_step")
            current_iteration = last_iteration + 1 if last_iteration else 0
            return current_iteration

        run_iter_count_step = run_iter_count()

        @task.branch(task_id="stopping_decision_step")
        def stopping_decision(max_iterations, ti=None):
            task_logger.debug("Entering")
            current_iteration = ti.xcom_pull(task_ids="run_iter_count_step")
            def is_stop_criteria_reached(iteration):
                if iteration >= max_iterations:
                    return True
                else:
                    return False

            task_logger.debug("Done")
            if is_stop_criteria_reached(current_iteration):
                return "stop_step"
            else:
                return "continue_step"

        stopping_conditional_step = stopping_decision(config.get('run').get('iterations').get('max'))

        continue_step = TriggerDagRunOperator(
                task_id='continue_step',
                trigger_dag_id=interaction_dag.dag_id,
                dag=interaction_dag
                )

        stop_step = EmptyOperator(task_id="stop_task", dag=interaction_dag)

        dump_config >> pull_step >> effectuation_step >> recon_step >> push_step >> run_iter_count_step >> stopping_conditional_step >> [continue_step, stop_step]

    return dag

