<!--
Copyright (c) 2019 Matthias Tafelmeier.

This file is part of godon

godon is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

godon is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this godon. If not, see <http://www.gnu.org/licenses/>.
-->
# Godon API

## api 

> micro infrastructure stack related logic

### api validate

> validate the openapi spec

~~~bash
set -eEux

docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli validate -i /local/openapi.yml
~~~

### api generate

> generate server stub from the openapi spec

~~~bash
set -eEux

docker run --rm -v "${MASKFILE_DIR}:/local" openapitools/openapi-generator-cli generate \
            -i /local/openapi.yml \
            --template-dir /local/templates/ \
            --generator-name python-flask \
            -o /local/flask

cp "${MASKFILE_DIR}"/controller.py ./flask/openapi_server/controllers/controller.py
cp "${MASKFILE_DIR}"/archive_db.py ./flask/openapi_server/controllers/archive_db.py
cp "${MASKFILE_DIR}"/meta_data_db.py ./flask/openapi_server/controllers/meta_data_db.py
touch ./flask/openapi_server/controllers/__init__.py

echo "apache-airflow-client == 2.3.0" >> ./flask/requirements.txt
echo "Jinja2 == 3.1.2" >> ./flask/requirements.txt
echo "psycopg2-binary == 2.9.7" >> ./flask/requirements.txt
~~~
