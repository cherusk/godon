
### --- definition coroutines --- ###
{% include 'nats_coroutines.py' %}
### --- end coroutines --- ###

def create_target_interaction_dag(dag_id, config, target, identifier):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder subdag for interacting with targets')

    with dag as interaction_dag:

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

            archive_db_engine = create_engine(f'postgresql://{ARCHIVE_DB_USER}:{ARCHIVE_DB_PASSWORD}@{ARCHIVE_DB_HOST}:{ARCHIVE_DB_PORT}/{ARCHIVE_DB_DATABASE}')
            task_logger.debug("Entering")

            metric_value = ti.xcom_pull(task_ids="recon_step")
            settings_full = ti.xcom_pull(task_ids="pull_optimization_step")

            setting_id = hashlib.sha256(str.encode(settings_full)).hexdigest()[0:6]

            task_logger.debug(f"Metric : f{metric_value}")

            metric_data = dict(metric=metric_value)
            msg = asyncio.run(send_msg_via_nats(subject=f'recon_{identifier}', data_dict=metric_data))

            breeder_table_name = config.get("name")

            query = f"INSERT INTO {breeder_table_name} VALUES ({setting_id}, {setting_full}, {setting_result});"

            archive_db_engine.execute(query)

            task_logger.debug("Done")

            return msg

        push_step = run_push_optimization()

        @dag.task(task_id="recon_step")
        def run_reconnaissance():

            task_logger.debug("Entering")
            prom_conn = PrometheusConnect(url=PROMETHEUS_URL,
                                          retry=urllib3.util.retry.Retry(total=3, raise_on_status=True, backoff_factor=0.5),
                                          disable_ssl=True)

            start_time = parse_datetime("2m")
            end_time = parse_datetime("now")
            chunk_size = timedelta(minutes=1)

            metric_data = dict()
            for objective in config.get('objectives'):
                recon_service_type = objective.get('reconaissance').get('service')

                if recon_service_type == 'prometheus':
                    recon_query = objective.get('reconaissance').get('query')
                    query_name = objective.get('reconaissance').get('name')
                    query_string = query.get('query')

                    query_result = prom_conn.custom_query(query_string)
                    metric_value = query_result[0]
                    metric_data[query_name] = metric_value.get('value')[1]
                else:
                    raise Exception("Reconnaisance service type {recon_service_type} not supported yet.")

            task_logger.debug("Done")

            return metric_data

        recon_step = run_reconnaissance()

        _ssh_hook = SSHHook(
            remote_host=target.get('address'),
            username=target.get('user'),
            key_file=target.get('key_file'),
            conn_timeout=30,
            keepalive_interval=10
        )

{% raw %}
        effectuation_step = SSHOperator(
            ssh_hook=_ssh_hook,
            task_id='effectuation',
            conn_timeout=30,
            command="""
                    {{ ti.xcom_pull(task_ids='pull_optimization_step') }}
                    """,
            dag=interaction_dag,
        )
{% endraw %}

        continue_step = TriggerDagRunOperator(
                task_id='continue_step',
                trigger_dag_id=interaction_dag.dag_id,
                dag=interaction_dag
                )

        pull_step >> effectuation_step >> recon_step >> push_step >> continue_step

    return dag

