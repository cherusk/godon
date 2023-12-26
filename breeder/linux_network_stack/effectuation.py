
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
            prom_conn = PrometheusConnect(url=PROMETHEUS_URL,
                                          retry=urllib3.util.retry.Retry(total=3, raise_on_status=True, backoff_factor=0.5),
                                          disable_ssl=True)

            metric_data = dict()
            for objective in config.get('objectives'):
                recon_service_type = objective.get('reconaissance').get('service')

                if recon_service_type == 'prometheus':
                    recon_query = objective.get('reconaissance').get('query')
                    query_name = objective.get('name')

                    query_result = prom_conn.custom_query(recon_query)

                    if query_result.get('resultType') != 'scalar':
                        raise Exception("Custom Query must be of result type scalar.")

                    # Example format of result processed
                    #   "data": {
                    #       "resultType": "scalar",
                    #       "result": [
                    #         1703619892.31, << TS
                    #         "0.401370548"  << Value
                    #       ]
                    #     }

                    value = metric_value.get('result')[1]

                    if value == "NaN":
                        raise Exception("Scalar reduction of custom query probably ailing, only returning NaN.")

                    metric_data[query_name] = value
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

