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
import time
import datetime
from pprint import pprint
from dateutil.parser import parse as dateutil_parser

import airflow_client.client as client
from airflow_client.client.api import dag_run_api
from airflow_client.client.model.dag_run import DAGRun
from airflow_client.client.model.error import Error
from airflow_client.client.model.list_dag_runs_form import ListDagRunsForm
from airflow_client.client.model.dag_run_collection import DAGRunCollection
from airflow_client.client.model.dag_state import DagState
from airflow_client.client.api import connection_api
from airflow_client.client.model.connection import Connection

from flask import abort
from flask import Response

from jinja2 import Environment, FileSystemLoader

import archive_db as archive
import meta_data_db as meta_data

AIRFLOW_API_BASE_URL = os.environ.get('AIRFLOW__URL')
AIRFLOW_API_VERSION = "v1"
AIRFLOW_API_AUTH_USER = "airflow"
AIRFLOW_API_AUTH_PW = "airflow"

DAG_TEMPLATES_DIR = "/usr/src/app/openapi_server/templates/"
DAG_DIR = "/usr/src/app/openapi_server/dags/"

ARCHIVE_DB_CONFIG = dict(user="yugabyte",
                         password="yugabyte",
                         host=os.environ.get('ARCHIVE_DB_HOSTNAME'),
                         port=os.environ.get('ARCHIVE_DB_PORT'))

META_DB_CONFIG = dict(user="meta_data",
                      password="meta_data",
                      host=os.environ.get('META_DB_HOSTNAME'),
                      port=os.environ.get('META_DB_PORT'))

breeders_db = dict()

configuration = client.Configuration(
    host = f"{AIRFLOW_API_BASE_URL}/api/{AIRFLOW_API_VERSION}",
    username = f"{AIRFLOW_API_AUTH_USER}",
    password = f"{AIRFLOW_API_AUTH_PW}"
)


def breeders_delete(content):  # noqa: E501
    """breeders_delete

    Purge a breeder # noqa: E501

    """

    api_response = dict(result=success)

    with client.ApiClient(configuration) as api_client:
        api_instance = dag_run_api.DAGRunApi(api_client)
        dag_id = content.get('name')
        dag_run_id = dag_id

        try:
            # Delete a DAG run
            api_instance.delete_dag_run(dag_id, dag_run_id)
        except client.ApiException as e:
            print("Exception when calling DAGRunApi->delete_dag_run: %s\n" % e)
            api_response = dict(result=failure)

    return api_response


def breeders_get():  # noqa: E501
    """breeders_get

    Provides info on configured breeders # noqa: E501

    """

    api_response = None

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

    api_response = None

    with client.ApiClient(configuration) as api_client:
        # Create an instance of the API class
       api_instance = dag_run_api.DAGRunApi(api_client)
       dag_id = name # str | The DAG ID.
       dag_run_id = name # str | The DAG run ID.

       try:
       # Get a DAG run
           api_response = api_instance.get_dag_run(dag_id, dag_run_id)
       except client.ApiException as e:
           print("Exception when calling DAGRunApi->get_dag_run: %s\n" % e)

    return api_response.to_dict()


def breeders_post(content):  # noqa: E501
    """breeders_post

    Create a breeder # noqa: E501

    """

    api_response = dict(connection=None, breeder=None)

    def create_breeder(api_client, content):
        api_instance = dag_run_api.DAGRunApi(api_client)
        breeder_id = content.get('breeder').get('name')
        breeder_config = dict(content)

        # templating related
        environment = Environment(loader=FileSystemLoader(DAG_TEMPLATES_DIR))
        template = environment.get_template("root_dag.py")
        filename = f"{DAG_DIR}/root_dag.py"
        rendered_dag = template.render(breeder_config)

        with open(filename, mode="w", encoding="utf-8") as dag_file:
            dag_file.write(rendered_dag)

        time.sleep(2) # wait as workaround until synchronous reload of dags implemented


        # extract config from request
        parallel_runs = breeder_config.get('run').get('parallel')
        targets = breeder_config.get('effectuation').get('targets')
        consolidation_probability = breeder_config.get('cooperation').get('consolidation').get('probability')
        dag_name = breeder_config.get('name')

        ## create knowledge archive db relevant state

        # set dbname to work with to breeder_id
        db_config = ARCHIVE_DB_CONFIG.copy()
        db_config.update(dict(dbname=breeder_id))

        __query = archive.queries.create_breeder_table(table_name=dag_name)
        archive.archive_db.__execute(db_info=db_config, query=__query)

        for target in targets:
            identifier = str(abs(hash(target.get('address'))))[0:6]
            for run_id in range(0, parallel_runs):
                dag_id = f'{dag_name}_{run_id}_{identifier}'

                __query = archive.queries.create_breeder_table(table_name=dag_id)
                archive.archive_db.__execute(db_info=db_config, query=__query)

                __query = archive.queries.create_procedure(procedure_name=f"{dag_id}_procedure",
                                                           probability=consolidation_probability,
                                                           source_table_name=dag_id,
                                                           target_table_name=dag_name)
                archive.archive_db.__execute(db_info=db_config, query=__query)

                __query = archive.queries.create_trigger(trigger_name="{dag_id}_trigger",
                                                         table_name=dag_id,
                                                         procedure_name="{dag_id}_procedure")
                archive.archive_db.__execute(db_info=db_config, query=__query)

        ## create and fill breeder meta data db
        db_config = META_DB_CONFIG.copy()
        db_config.update(dict(dbname=breeder_id))
        db_table_name = 'breeder_meta_data'

        __query = meta_data.queries.create_meta_breeder_table(table_name=db_table_name)
        archive.archive_db.__execute(db_info=db_config, query=__query)

        __query = meta_data.queries.insert_breeder_meta(table_name=db_table_name,
                                                      creation_ts=datetime.datetime.now(),
                                                      meta_state=breeder_config)
        archive.archive_db.__execute(db_info=db_config, query=__query)


    with client.ApiClient(configuration) as api_client:
        # Do not create connection dynamically for now
        #api_response['breeder'] = create_breeder(api_client, content).to_dict()
        create_breeder(api_client, content)

    return Response(dict(), status=200, mimetype='application/json')


def breeders_put(content):  # noqa: E501
    """breeders_put

    Update a breeder configuration # noqa: E501

    """
    abort(501, description="Not Implemented")
