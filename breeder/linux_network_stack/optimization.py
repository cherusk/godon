
def objective(trial):

###--- definition coroutines ---###
### We have to keep to coroutines in the objective function,
### otherwise the workers do not know about those until we preinstall those.
{% raw %}
    async def do_effectuation(settings):
        import time
        import nats
        import sys
        # Connect to NATS Server.
        nc = await nats.connect(NATS_SERVER_URL)
        settings_data = dict(settings=settings)
        transmit_data = bytes(json.dumps(settings_data), encoding='utf8')
        while True:
            try:
                response = await nc.request('effectuation', transmit_data)
                print('Response:', response )
                break
            except nats.errors.NoRespondersError:
                time.sleep(2)
                continue
            except:
                logger.warning('unexpted exception')
                logger.warning(sys.exc_info()[0])
                raise
        await nc.flush()
        await nc.close()
{% endraw %}

    async def gather_recon():
        # Connect to NATS Server.
        nc = await nats.connect(NATS_SERVER_URL)
        sub = await nc.subscribe('recon')
        msg = await sub.next_msg(timeout=300)
        print(msg)
        await msg.respond(b'OK')
        await nc.close()
        return msg.data.decode()
###--- end coroutines ---###

    import logging
    logger = logging.getLogger('objective')
    logger.setLevel(logging.DEBUG)

    logger.warning('entering')

    # Compiling settings for effectuation
    settings = []
    for setting_name, setting_config in config.get('settings').get('sysctl').items():
        constraints = setting_config.get('constraints')
        suggested_value = trial.suggest_int(setting_name, constraints.get('lower') , constraints.get('upper') )
        if setting_name in ['net.ipv4.tcp_rmem', 'net.ipv4.tcp_wmem']:
            settings.append(f"sudo sysctl -w {setting_name}='4096 131072 {suggested_value}';")
        else:
            settings.append(f"sudo sysctl -w {setting_name}='{suggested_value}';")
    settings = '\n'.join(settings)

    logger.warning('doing effectuation')
    asyncio.run(do_effectuation(settings))

    logger.warning('gathering recon')
    metric = json.loads(asyncio.run(gather_recon()))
    metric_value = metric.get('metric')
    rtt = float(metric_value['tcp_rtt'])
    delivery_rate = float(metric_value['tcp_delivery_rate_bytes'])
    logger.warning(f'metric received {metric_value}')

    logger.warning('Done')

    return rtt, delivery_rate



def create_optimization_dag(dag_id, config):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder subdag for optimizing \
                    linux network stack dynamics')

    with dag as optimization_dag:

        dump_config = BashOperator(
            task_id='print_config',
            bash_command='echo ${config}',
            env={"config": str(config)},
            dag=optimization_dag,
        )

        ## perform optimiziation run
        @dag.task(task_id="optimization_step")
        def run_optimization():

            with Client(address="godon_dask_scheduler_1:8786") as client:
                # Create a study using Dask-compatible storage
                storage = DaskStorage(InMemoryStorage())
                study = optuna.create_study(directions=["minimize", "maximize"], storage=storage)
                # Optimize in parallel on your Dask cluster
                futures = [
                    client.submit(study.optimize, objective, n_trials=10, pure=False)
                ]
                wait(futures, timeout=7200)
                print(f"Best params: {study.best_params}")

        optimization_step = run_optimization()

        dump_config >> optimization_step

    return dag
