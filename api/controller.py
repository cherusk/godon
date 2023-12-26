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
import hashlib
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

import openapi_server.controllers.archive_db as archive
import openapi_server.controllers.meta_data_db as meta_data

import logging

import json
import uuid


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


def breeders_id_delete(breeder_id):  # noqa: E501
    """breeders_delete

    Purge a breeder # noqa: E501

    """

    # cleanup dag definition config file
    filename = f"{DAG_DIR}/{breeder_id}.py"

    if os.path.exists(filename):
        os.remove(filename)

    time.sleep(2) # wait as workaround until synchronous reload of dags implemented

    ## cleanup knowledge archive db relevant state

    # set dbname to work with to breeder_id
    db_config = ARCHIVE_DB_CONFIG.copy()
    db_config.update(dict(dbname="archive_db"))

    __query = archive.queries.delete_breeder_table(table_name=breeder_id)
    archive.archive_db.execute(db_info=db_config, query=__query)

    __query = archive.queries.fetch_procedures(breeder_id=breeder_id)
    procedures = archive.archive_db.execute(db_info=db_config, query=__query, with_result=True)

    for procedure_name in procedures:
        logging.error(type(procedure_name))
        logging.error(procedure_name)
        __query = archive.queries.delete_procedure(procedure_name=procedure_name[0])
        archive.archive_db.execute(db_info=db_config, query=__query)

    __query = archive.queries.fetch_tables(breeder_id=breeder_id)
    archive_tables = archive.archive_db.execute(db_info=db_config, query=__query, with_result=True)

    for table_name in archive_tables:
        logging.error(table_name)
        __query = archive.queries.delete_breeder_table(table_name=table_name[0])
        archive.archive_db.execute(db_info=db_config, query=__query)


    ## cleanup breeder meta data db state
    db_config = META_DB_CONFIG.copy()
    db_config.update(dict(dbname='meta_data'))
    db_table_name = 'breeder_meta_data'

    __query = meta_data.queries.remove_breeder_meta(table_name=db_table_name,
                                                    breeder_id=breeder_id)
    archive.archive_db.execute(db_info=db_config, query=__query)

    return Response(json.dumps(dict(message=f"Purged Breeder named {breeder_id}")),
                    status=200,
                    mimetype='application/json')


def breeders_get():  # noqa: E501
    """breeders_get

    Provides info on configured breeders # noqa: E501

    """
    configured_breeders = list()

    ## fetch breeder meta data list
    db_config = META_DB_CONFIG.copy()
    db_config.update(dict(dbname='meta_data'))
    db_table_name = 'breeder_meta_data'

    __query = meta_data.queries.fetch_breeders_list(table_name=db_table_name)
    breeder_meta_data_list = archive.archive_db.execute(db_info=db_config, query=__query, with_result=True)

    # preformat timestamp to be stringifyable
    configured_breeders = [(breeder_row[0],breeder_row[1].isoformat()) for breeder_row in breeder_meta_data_list]

    logging.error(json.dumps(configured_breeders))

    return Response(response=json.dumps(configured_breeders),
                    status=200,
                    mimetype='application/json')


def breeders_id_get(breeder_uuid):  # noqa: E501
    """breeders_name_get

    Obtain information about breeder from its name # noqa: E501

    """

    ## fetch breeder meta data
    db_config = META_DB_CONFIG.copy()
    db_config.update(dict(dbname='meta_data'))
    db_table_name = 'breeder_meta_data'

    __query = meta_data.queries.fetch_meta_data(table_name=db_table_name, breeder_id=breeder_uuid)
    breeder_meta_data = archive.archive_db.execute(db_info=db_config, query=__query, with_result=True)

    breeder_meta_data_row = breeder_meta_data[0]

    return Response(response=json.dumps(dict(creation_timestamp=breeder_meta_data_row[0].isoformat(),
                                             breeder_definition=breeder_meta_data_row[1])),

                    status=200,
                    mimetype='application/json')

def breeders_post(content):  # noqa: E501
    """breeders_post

    Create a breeder # noqa: E501

    """


    breeder_config_full = content
    breeder_config = dict(content.get('breeder'))
    breeder_name = breeder_config.get('name')
    uuid = uuid.uuid4()
    config.update(dict(uuid=uuid))

    def create_breeder(api_client, content):

        # templating related
        environment = Environment(loader=FileSystemLoader(DAG_TEMPLATES_DIR))
        template = environment.get_template("root_dag.py")
        filename = f"{DAG_DIR}/{breeder_id}.py"
        rendered_dag = template.render(breeder_config_full)

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
        db_config.update(dict(dbname="archive_db"))

        __query = archive.queries.create_breeder_table(table_name=uuid)
        archive.archive_db.execute(db_info=db_config, query=__query)

        for target in targets:
            hash_suffix = hashlib.sha256(str.encode(target.get('address'))).hexdigest()[0:6]
            for run_id in range(0, parallel_runs):
                dag_id = f'{uuid}_{run_id}_{hash_suffix}'

                __query = archive.queries.create_breeder_table(table_name=dag_id)
                archive.archive_db.execute(db_info=db_config, query=__query)

                __query = archive.queries.create_procedure(procedure_name=f'{dag_id}_procedure',
                                                           probability=consolidation_probability,
                                                           source_table_name=dag_id,
                                                           target_table_name=dag_name)
                archive.archive_db.execute(db_info=db_config, query=__query)

                __query = archive.queries.create_trigger(trigger_name=f'{dag_id}_trigger',
                                                         table_name=dag_id,
                                                         procedure_name=f'{dag_id}_procedure')
                archive.archive_db.execute(db_info=db_config, query=__query)

        ## create and fill breeder meta data db
        db_config = META_DB_CONFIG.copy()
        db_config.update(dict(dbname='meta_data'))
        db_table_name = 'breeder_meta_data'

        __query = meta_data.queries.create_meta_breeder_table(table_name=db_table_name)
        archive.archive_db.execute(db_info=db_config, query=__query)

        __query = meta_data.queries.insert_breeder_meta(table_name=db_table_name,
                                                      breeder_id=uuid,
                                                      creation_ts=datetime.datetime.now(),
                                                      meta_state=breeder_config)
        archive.archive_db.execute(db_info=db_config, query=__query)


    with client.ApiClient(configuration) as api_client:
        # Do not create connection dynamically for now
        #api_response['breeder'] = create_breeder(api_client, content).to_dict()
        create_breeder(api_client, content)

    return Response(json.dumps(dict(message=f"Created Breeder named {breeder_id}")),
                               status=200,
                               mimetype='application/json')


def breeders_put(content):  # noqa: E501
    """breeders_put

    Update a breeder configuration # noqa: E501

    """
    abort(501, description="Not Implemented")
