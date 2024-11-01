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


from datetime import timedelta

import random
import logging
import json
import copy
import hashlib
import os

import pals
import asyncio
import urllib3

import optuna
from optuna.storages import InMemoryStorage
from optuna.integration import DaskStorage
from distributed import Client, wait

from sqlalchemy import create_engine
from sqlalchemy import text

from prometheus_api_client import PrometheusConnect, MetricsList, Metric
from prometheus_api_client.utils import parse_datetime

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

NATS_SERVER_URL = os.environ.get("NATS_SERVER_URL")

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL")

DASK_OPTUNA_SCHEDULER_URL = os.environ.get("DASK_OPTUNA_SCHEDULER_URL")

DLM_DB_USER = os.environ.get("DLM_DB_USER")
DLM_DB_PASSWORD = os.environ.get("DLM_DB_PASSWORD")
DLM_DB_HOST = os.environ.get("DLM_DB_HOST")
DLM_DB_DATABASE = os.environ.get("DLM_DB_DATABASE")
DLM_DB_CONNECTION = f"postgresql://{DLM_DB_USER}:{DLM_DB_PASSWORD}@{DLM_DB_HOST}/{DLM_DB_DATABASE}"


ARCHIVE_DB_USER = os.environ.get("ARCHIVE_DB_USER")
ARCHIVE_DB_PASSWORD = os.environ.get("ARCHIVE_DB_PASSWORD")
ARCHIVE_DB_HOSTNAME = os.environ.get("ARCHIVE_DB_HOSTNAME")
ARCHIVE_DB_PORT = os.environ.get("ARCHIVE_DB_PORT")
ARCHIVE_DB_DATABASE = os.environ.get("ARCHIVE_DB_DATABASE")

###

{% include 'effectuation.py' %}

{% include 'optimization.py' %}

config = {{ breeder }}

parallel_runs = config.get('run').get('parallel')
targets = config.get('effectuation').get('targets')
dag_name = config.get('uuid')
is_cooperative = config.get('cooperation').get('active')

target_id = 0

def determine_config_shard(run_id=None,
                           target_id=None,
                           config=None,
                           targets_count=0,
                           parallel_runs_count=0):

    config_result = copy.deepcopy(config)
    settings_space = config_result.get('settings').get('sysctl')

    for setting in settings_space.items():
        upper = setting.get('constraints').get('upper')
        lower = setting.get('constraints').get('lower')

        delta = abs(upper - lower)

        shard_size = delta / targets_count * parallel_runs_count

        setting['constraints']['lower'] = lower + shard_size * (run_id + target_id)

    config_result['settings']['sysctl'] = settings_space

    return config_result


for target in targets:
    hash_suffix = hashlib.sha256(str.encode(target.get('address'))).hexdigest()[0:6]

    for run_id in range(0, parallel_runs):
        dag_id = f'{dag_name}_{run_id}'
        if not is_cooperative:
            config = determine_config_shard()
        globals()[f'{dag_id}_optimization_{hash_suffix}'] = create_optimization_dag(f'{dag_id}_optimization_{hash_suffix}', config, run_id, hash_suffix)
        globals()[f'{dag_id}_target_{hash_suffix}'] = create_target_interaction_dag(f'{dag_id}_target_interaction_{hash_suffix}', config, target, hash_suffix)

    target_id += 1
