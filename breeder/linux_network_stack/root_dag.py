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
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.contrib.hooks.ssh_hook import SSHHook
from airflow.models import Variable
from airflow.utils.dates import days_ago

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


def create_dag(dag_id):

    dag = DAG(dag_id,
              default_args=DEFAULTS,
              description='breeder geared to optimizing \
                    linux network stack dynamics')

    with dag:
        # perform reconnaisance at target instance
        recon_step = BashOperator(
            task_id='reconnaisance',
            bash_command='echo noop',
            dag=net_stack_dag,
        )

        # perform optimiziation run
        optimizing_step = BashOperator(
            task_id='optimize',
            bash_command='echo noop',
            dag=net_stack_dag,
        )

        # perform config effectuation at target instance
        conn_hook = SSHHook(
                remote_host=Variable.get("target"),
                username='root',
                key_file="/opt/airflow/credentials/id_rsa",
                timeout=30,
                keepalive_interval=10
                )

        effectuation_step = SSHOperator(
            ssh_hook=conn_hook,
            remote_host=Variable.get("target"),
            task_id='effectuation',
            timeout=30,
            command="""
                    sysctl -w net.ipv4.tcp_mem="188760 251683	377520";
                    sysctl -w net.ipv4.tcp_rmem="4096	131072	6291456";
                    sysctl -w net.ipv4.tcp_wmem="4096	131072	6291456";
                    sysctl -w net.core.netdev_budget=300;
                    sysctl -w net.core.netdev_max_backlog=1000;
                    """,
            dag=net_stack_dag,
        )

        recon_step >> optimizing_step >> effectuation_step

dag_id = 'linux_network_stack_breeder'
globals()[dag_id] = create_dag(dag_id)
