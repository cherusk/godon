#
# Copyright (c) 2019 Matthias Tafelmeier.
#
# This file is part of godon
#
# godon is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# godon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this godon. If not, see <http://www.gnu.org/licenses/>.
#

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.empty import EmptyOperator
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.contrib.hooks.ssh_hook import SSHHook
from airflow.models import Variable
from airflow.utils.dates import days_ago

import optuna
from optuna.storages import InMemoryStorage
from optuna.integration import DaskStorage
from distributed import Client, wait

from prometheus_api_client import PrometheusConnect, MetricsList, Metric
from prometheus_api_client.utils import parse_datetime
from datetime import timedelta

from airflow.decorators import task

DEFAULTS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'retries': 0,
    'trigger_rule': 'all_success'
    # 'email': ['airflow@example.com'],
    # 'email_on_failure': False,
    # 'email_on_retry': False,
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    }


def create_dag(dag_id, config):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder geared to optimizing \
                    linux network stack dynamics')

    with dag as net_dag:

        dump_config = BashOperator(
            task_id='print_config',
            bash_command='echo ${config}',
            env={"config": config},
            dag=net_dag,
        )

        # Conceptual outline

        @dag.task(task_id="recon_step")
        def run_reconnaissance():
            prom_conn = PrometheusConnect(url ="http://godon_prometheus_1:9090", disable_ssl=True)

            start_time = parse_datetime("2m")
            end_time = parse_datetime("now")
            chunk_size = timedelta(minutes=1)

            metric_data = prom_conn.get_metric_range_data(
                    metric_name="tcp_rtt",
                    start_time=start_time,
                    end_time=end_time,
                    chunk_size=chunk_size,
                    )

            metric_object_list = MetricsList(metric_data)

            for item in metric_object_list:
                print(item.metric_name, item.label_config, "\n")

        recon_step = run_reconnaissance()

        ## perform optimiziation run
        @dag.task(task_id="optimization_step")
        def run_optimization():
            # boilerplate from https://jrbourbeau.github.io/dask-optuna/

            def objective(trial):
                x = trial.suggest_uniform("x", -10, 10)
                return (x - 2) ** 2

            with Client(address="godon_dask_scheduler_1:8786") as client:
                # Create a study using Dask-compatible storage
                storage = DaskStorage(InMemoryStorage())
                study = optuna.create_study(storage=storage)
                # Optimize in parallel on your Dask cluster
                futures = [
                    client.submit(study.optimize, objective, n_trials=10, pure=False)
                    for i in range(10)
                ]
                wait(futures)
                print(f"Best params: {study.best_params}")

        optimization_step = run_optimization()

        ## perform config effectuation at target instance
        _ssh_hook = SSHHook(
            remote_host=config.get('effectuation').get('target'),
            username=config.get('effectuation').get('user'),
            key_file=config.get('effectuation').get('key_file'),
            timeout=30,
            keepalive_interval=10
        )

        effectuation_step = SSHOperator(
            ssh_hook=_ssh_hook,
            task_id='effectuation',
            timeout=30,
            command="""
                    sudo sysctl -w net.ipv4.tcp_mem="188760 251683	377520";
                    sudo sysctl -w net.ipv4.tcp_rmem="4096	131072	6291456";
                    sudo sysctl -w net.ipv4.tcp_wmem="4096	131072	6291456";
                    sudo sysctl -w net.core.netdev_budget=300;
                    sudo sysctl -w net.core.netdev_max_backlog=1000;
                    """,
            dag=net_dag,
        )

        @task.branch(task_id="stopping_decision_step")
        def stopping_decision():
            def is_stop_criteria_reached():
                return True

            if is_stop_criteria_reached:
                return "stop_step"
            else:
                return "continue_step"

        stopping_conditional_step = stopping_decision()

        continue_step = TriggerDagRunOperator(
                task_id='continue_step',
                trigger_dag_id=net_dag.dag_id,
                dag=net_dag
                )

        stop_step = EmptyOperator(task_id="stop_task", dag=net_dag)

        dump_config >> recon_step  >> optimization_step >> effectuation_step >> stopping_conditional_step >> [continue_step, stop_step]

    return dag

###

config = {{ breeder }}

parallel_runs = config.get('run').get('parallel')
breeder_name = config.get('name')

for run_id in range(0, parallel_runs):
    for dag in config.get('dags'):
        dag_name = dag.get('name')
        dag_id = f'{dag_name}_run_id'
        globals()[dag_id] = create_dag(breeder_name, dag_id, config)
