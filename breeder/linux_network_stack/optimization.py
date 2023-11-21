

def create_optimization_dag(dag_id, config, identifier):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder subdag for optimizing \
                    linux network stack dynamics')

    with dag as optimization_dag:

        ## perform optimiziation run
        @dag.task(task_id="optimization_step")
        def run_optimization():

###--- definition objective ---###
### We have to keep the objective in the optuna invoking code scope,
### otherwise the dask distributed pickling will fail.
    {% macro local_objective_includ() %}{% include 'objective.py' %}{% endmacro %}
    {{ local_objective_includ()|indent(12) }} # default is indent of 4 spaces!
###--- end coroutines ---###

            objective_kwargs = dict(archive_db_url=f'postgresql://{ARCHIVE_DB_USER}:{ARCHIVE_DB_PASSWORD}@{ARCHIVE_DB_HOSTNAME}:{ARCHIVE_DB_PORT}/{ARCHIVE_DB_DATABASE}',
                                    locking_db_url=DLM_DB_CONNECTION,
                                    identifier=identifier,
                                    breeder_name=config.get('name'),
                                    )

            __directions = list()

            for __objective in config.get('objectives'):
                direction = __objective.get('direction')
                __directions.append(direction)

            with Client(address=DASK_OPTUNA_SCHEDULER_URL) as client:
                # Create a study using Dask-compatible storage
                storage = DaskStorage(InMemoryStorage())
                study = optuna.create_study(directions=__directions, storage=storage)
                objective_wrapped = lambda trial: objective(trial, **objective_kwargs)
                # Optimize in parallel on your Dask cluster
                futures = [
                    client.submit(study.optimize, objective_wrapped, n_trials=10, pure=False)
                ]
                wait(futures, timeout=7200)

        optimization_step = run_optimization()

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

        continue_step = TriggerDagRunOperator(
                task_id='continue_step',
                trigger_dag_id=optimization_dag.dag_id,
                dag=optimization_dag
                )

        stopping_conditional_step = stopping_decision(config.get('run').get('iterations').get('max'))

        stop_step = EmptyOperator(task_id="stop_task", dag=optimization_dag)

        optimization_step >> run_iter_count_step  >> stopping_conditional_step >> [continue_step, stop_step]

    return dag
