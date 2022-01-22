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

> validate server stub from the openapi spec

~~~bash
set -eEux

docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate \
            -i /local/openapi.yml \
            --generator-name python-flask \
            -o /local/flask
~~~
