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


import requests
import os
from pprint import pprint
from dateutil.parser import parse as dateutil_parser

import airflow_client.client as client
from airflow_client.client.api import dag_run_api
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.model.error import Error
from airflow_client.client.model.list_dag_runs_form import ListDagRunsForm
from airflow_client.client.model.dag_run_collection import DAGRunCollection
from airflow_client.client.model.dag_state import DagState


AIRFLOW_API_BASE_URL = os.environ.get('AIRFLOW__URL')
AIRFLOW_API_VERSION = "v1"
AIRFLOW_API_AUTH_USER = "airflow"
AIRFLOW_API_AUTH_PW = "airflow"

breeders_db = dict()


def breeders_delete(content):  # noqa: E501
    """breeders_delete

    Purge a breeder # noqa: E501

    """

    breeder_id = content.get('name')
    url = f'{AIRFLOW_API_BASE_URL}/dags/{breeder_id}/dagRuns/{breeder_id}'
    response = requests.delete(url)

    return response


def breeders_get():  # noqa: E501
    """breeders_get

    Provides info on configured breeders # noqa: E501

    """

    api_response = None
    configuration = client.Configuration(
        host = f"{AIRFLOW_API_BASE_URL}/api/{AIRFLOW_API_VERSION}",
        username = f"{AIRFLOW_API_AUTH_USER}",
        password = f"{AIRFLOW_API_AUTH_PW}"
    )

    with client.ApiClient(configuration) as api_client:
        api_instance = dag_run_api.DAGRunApi(api_client)

        list_dag_runs_form = ListDagRunsForm(
            #order_by="order_by_example",
            page_offset=0,
            page_limit=10000,
            dag_ids=[
                "linux_network_stack_breeder", # only one dag existing so far
            ],
            #states=[
            #],
            execution_date_gte=dateutil_parser('1970-01-01T00:00:00.00Z'),
            execution_date_lte=dateutil_parser('1970-01-01T00:00:00.00Z'),
            start_date_gte=dateutil_parser('1970-01-01T00:00:00.00Z'),
            start_date_lte=dateutil_parser('1970-01-01T00:00:00.00Z'),
            end_date_gte=dateutil_parser('1970-01-01T00:00:00.00Z'),
            end_date_lte=dateutil_parser('1970-01-01T00:00:00.00Z'),
        ) # ListDagRunsForm |

        # example passing only required values which don't have defaults set
        try:
           # List DAG runs (batch)
           api_response = api_instance.get_dag_runs_batch(list_dag_runs_form)
        except client.ApiException as e:
           pprint("Exception when calling DAGRunApi->get_dag_runs_batch: %s\n" % e)
           raise e

    return api_response.to_dict()


def breeders_name_get(name):  # noqa: E501
    """breeders_name_get

    Obtain information about breeder from its name # noqa: E501

    """

    breeder_id = content.get('name')
    url = f'{AIRFLOW_API_BASE_URL}/dags/{breeder_id}'
    response = requests.delete(url)

    return response


def breeders_post(content):  # noqa: E501
    """breeders_post

    Create a breeder # noqa: E501

    """

    api_response = None
    configuration = client.Configuration(
        host = f"{AIRFLOW_API_BASE_URL}/api/{AIRFLOW_API_VERSION}",
        username = f"{AIRFLOW_API_AUTH_USER}",
        password = f"{AIRFLOW_API_AUTH_PW}"
    )

    with client.ApiClient(configuration) as api_client:
        api_instance = dag_run_api.DAGRunApi(api_client)
        breeder_id = content.get('breeder').get('name')
        breeder_config = dict(content)

        dag_run = DAGRun(
            dag_run_id=breeder_id ,
            #state=DagState("queued"),
            conf=breeder_config,
        ) # DAGRun |

        try:
            # Trigger a new DAG run
            api_response = api_instance.post_dag_run(breeder_id, dag_run)
        except client.ApiException as e:
            print("Exception when calling DAGRunApi->post_dag_run: %s\n" % e)
            raise e

    return api_response.to_dict()


def breeders_put(content):  # noqa: E501
    """breeders_put

    Update a breeder configuration # noqa: E501

    """

    breeder_id = content.get('name')
    url = f'{AIRFLOW_API_BASE_URL}/dags/{breeder_id}/dagRuns/{breeder_id}'
    response = requests.patch(url)

    return response

