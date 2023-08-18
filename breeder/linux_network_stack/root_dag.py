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

from sqlalchemy import create_engine
from sqlalchemy import text

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

NATS_SERVER_URL = "nats://godon_nats_1:4222"


ARCHIVE_DB_ENGINE = create_engine(f'postgresql://{ARCHIVE_DB_USER}:{ARCHIVE_DB_PASSWORD}@{ARCHIVE_DB_HOST}:{ARCHIVE_DB_PORT}/{ARCHIVE_DB_DATABASE}')

###

{% include 'effectuation.py' %}

{% include 'optimization.py' %}

config = {{ breeder }}

parallel_runs = config.get('run').get('parallel')
targets = config.get('effectuation').get('targets')
dag_name = config.get('name')

for target in targets:
    identifier = str(abs(hash(target.get('address'))))[0:6]
    for run_id in range(0, parallel_runs):
        dag_id = f'{dag_name}_{run_id}'
        globals()[f'{dag_id}_optimization_{identifier}'] = create_optimization_dag(f'{dag_id}_optimization_{identifier}', config, identifier)
        globals()[f'{dag_id}_target_{identifier}'] = create_target_interaction_dag(f'{dag_id}_target_interaction_{identifier}', config, target, identifier)
