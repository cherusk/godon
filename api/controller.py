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


AIRFLOW_API_BASE_URL = "http://TBD"


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

    url = f'{AIRFLOW_API_BASE_URL}/dags'
    response = requests.get(url)

    return response


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

    breeder_id = content.get('name')
    url = f'{AIRFLOW_API_BASE_URL}/dags/{breeder_id}/dagRuns'
    response = requests.post(url)

    return response


def breeders_put(content):  # noqa: E501
    """breeders_put

    Update a breeder configuration # noqa: E501

    """

    breeder_id = content.get('name')
    url = f'{AIRFLOW_API_BASE_URL}/dags/{breeder_id}/dagRuns/{breeder_id}'
    response = requests.patch(url)

    return response

