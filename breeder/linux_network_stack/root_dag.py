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
from airflow.decorators import task

import optuna
from optuna.storages import InMemoryStorage
from optuna.integration import DaskStorage
from distributed import Client, wait

from prometheus_api_client import PrometheusConnect, MetricsList, Metric
from prometheus_api_client.utils import parse_datetime
from datetime import timedelta
import asyncio

import nats
import time
import sys

import random
import logging
import json


task_logger = logging.getLogger("airflow.task")
task_logger.setLevel(logging.DEBUG)

DEFAULTS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 0,
    'trigger_rule': 'all_success',
    'schedule_interval': None
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

## coroutines
NATS_SERVER_URL = "nats://godon_nats_1:4222"
# interaction
async def gather_instruction():
    # Connect to NATS Server.
    nc = await nats.connect(NATS_SERVER_URL)
    sub = await nc.subscribe('effectuation')
    msg = await sub.next_msg(timeout=300)
    print(msg)
    await msg.respond(b'OK')
    await nc.close()
    return msg.data.decode()

{% raw %}
async def deliver_probe(metric_value):
    # Connect to NATS Server.
    nc = await nats.connect(NATS_SERVER_URL)
    metric_data = dict(metric=metric_value)
    transmit_data = bytes(json.dumps(metric_data), encoding='utf8')
    while True:
        try:
            response = await nc.request('recon', transmit_data)
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
# optimization


def create_target_interaction_dag(dag_id, config):

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

            msg = asyncio.run(gather_instruction())
            settings = json.loads(msg).get('settings')

            task_logger.debug(f"Settings: f{settings}")

            return settings

        pull_step = run_pull_optimization()

        @dag.task(task_id="push_optimization_step")
        def run_push_optimization(ti=None):
            task_logger.debug("Entering")

            metric_value = int(ti.xcom_pull(task_ids="recon_step"))

            task_logger.debug(f"Metric : f{metric_value}")

            msg = asyncio.run(deliver_probe(metric_value))

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

            metric_data = prom_conn.custom_query("quantile(0.5, tcp_rtt)") # get median

            task_logger.debug("Done")

            return metric_data[0]

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

            def objective(trial):
                import logging
                logger = logging.getLogger('objective')
                logger.setLevel(logging.DEBUG)
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


                x = trial.suggest_uniform("x", -10, 10)

                settings = """
                    sudo sysctl -w net.ipv4.tcp_rmem="4096	131072	6291456";
                    sudo sysctl -w net.ipv4.tcp_wmem="4096	131072	6291456";
                    sudo sysctl -w net.core.netdev_budget=300;
                    sudo sysctl -w net.core.netdev_max_backlog=1000;
                """
                logger.warning('entering')

                logger.warning('doing effectuation')
                asyncio.run(do_effectuation(settings))
                logger.warning('gathering recon')
                metric = json.loads(asyncio.run(gather_recon()))
                metric_value = metric.get('metric')
                logger.warning(f'metric received {metric_value}')
                logger.warning('Done')

                return metric_value

            with Client(address="godon_dask_scheduler_1:8786") as client:
                # Create a study using Dask-compatible storage
                storage = DaskStorage(InMemoryStorage())
                study = optuna.create_study(storage=storage)
                # Optimize in parallel on your Dask cluster
                futures = [
                    client.submit(study.optimize, objective, n_trials=10, pure=False)
                ]
                wait(futures, timeout=7200)
                print(f"Best params: {study.best_params}")

        optimization_step = run_optimization()

        dump_config >> optimization_step

    return dag

###

config = {{ breeder }}

parallel_runs = config.get('run').get('parallel')
dag_name = config.get('name')

for run_id in range(0, parallel_runs):
    dag_id = f'{dag_name}_{run_id}'
    globals()[f'{dag_id}_optimization'] = create_optimization_dag(f'{dag_id}_optimization', config)
    globals()[f'{dag_id}_target_interaction'] = create_target_interaction_dag(f'{dag_id}_target_interaction', config)
