

def create_optimization_dag(dag_id, config, identifier):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder subdag for optimizing \
                    linux network stack dynamics')

    with dag as optimization_dag:

        noop = BashOperator(
            task_id='noop',
            bash_command='echo "noop"',
            dag=optimization_dag,
        )

        ## perform optimiziation run
        @dag.task(task_id="optimization_step")
        def run_optimization():

###--- definition objective ---###
### We have to keep the objective in the optuna invoking code scope,
### otherwise the dask distributed pickling will fail.
    {% macro local_objective_includ() %}{% include 'objective.py' %}{% endmacro %}
    {{ local_objective_includ()|indent(12) }} # default is indent of 4 spaces!
###--- end coroutines ---###

            archive_db_url = f'postgresql://{ARCHIVE_DB_USER}:{ARCHIVE_DB_PASSWORD}@{ARCHIVE_DB_HOST}:{ARCHIVE_DB_PORT}/{ARCHIVE_DB_DATABASE}'
            __directions = list()

            for __objective in config.get('objectives'):
                direction = __objective.get('direction')
                __directions.append(direction)

            with Client(address=DASK_SERVER_ENDPOINT) as client:
                # Create a study using Dask-compatible storage
                storage = DaskStorage(InMemoryStorage())
                study = optuna.create_study(directions=__directions, storage=storage)
                objective_wrapped = lambda trial: objective(trial,identifier, archive_db_url)
                # Optimize in parallel on your Dask cluster
                futures = [
                    client.submit(study.optimize, objective_wrapped, n_trials=10, pure=False)
                ]
                wait(futures, timeout=7200)

        optimization_step = run_optimization()

        noop >> optimization_step

    return dag
