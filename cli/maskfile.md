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
# Godon CLI

## breeder

### breeder list

**OPTIONS**
* hostname
    * flags: --hostname
    * type: string
    * desc: godon hostname
* port
    * flags: --port
    * type: number
    * desc: godon port
* api_version
    * flags: --api-version
    * type: string
    * desc: godon api version


> List all configured breeders

~~~bash
set -eEux

__api_version="${api_version:-v0}"

curl --request GET "http://${hostname}:${port}/${__api_version}/breeders"
~~~

### breeder create

**OPTIONS**
* file
    * flags: --file
    * type: string
    * desc: definition file of breeder to be created
* hostname
    * flags: --hostname
    * type: string
    * desc: godon hostname
* port
    * flags: --port
    * type: number
    * desc: godon port
* api_version
    * flags: --api-version
    * type: string
    * desc: godon api version

> Create a breeder

~~~bash
set -eEux

__api_version="${api_version:-v0}"
__file="${file}"
__temp_file_json_tranfer="$(mktemp)"

cat "${__file}" | python -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin), sys.stdout, indent=4)' > "${__temp_file_json_tranfer}"

curl --request POST \
     -H 'Content-Type: application/json' \
     --data @"${__temp_file_json_tranfer}" \
     "http://${hostname}:${port}/${__api_version}/breeders"
~~~

### breeder purge

**OPTIONS**
* name
    * flags: --name
    * type: string
    * desc: name of breeder to be purged
* hostname
    * flags: --hostname
    * type: string
    * desc: godon hostname
* port
    * flags: --port
    * type: number
    * desc: godon port
* api_version
    * flags: --api-version
    * type: string
    * desc: godon api version

> Purge a breeder

~~~bash
set -eEux

__api_version="${api_version:-v0}"

curl --request DELETE \
     -H 'Content-Type: application/json' \
     --data "{ \"name\": \"${name}\" }" \
     "http://${hostname}:${port}/${__api_version}/breeders"
~~~

### breeder update

**OPTIONS**
* definition
    * flags: --file
    * type: string
    * desc: definition file of breeder to be updated
* hostname
    * flags: --hostname
    * type: string
    * desc: godon hostname
* port
    * flags: --port
    * type: number
    * desc: godon port
* api_version
    * flags: --api-version
    * type: string
    * desc: godon api version

> Update a breeder

~~~bash

set -eEux

__api_version="${api_version:-v0}"
__temp_file_json_tranfer="$(mktemp)"

cat "${file}" | python -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin), sys.stdout, indent=4)' > "${__temp_file_json_tranfer}"

curl --request PUT \
     -H 'Content-Type: application/json' \
     --data @"${__temp_file_json_tranfer}" \
     "http://${hostname}:${port}/${__api_version}/breeders"
~~~

### breeder show

**OPTIONS**
* name
    * flags: --name
    * type: string
    * desc: name of breeder to get details from
* hostname
    * flags: --hostname
    * type: string
    * desc: godon hostname
* port
    * flags: --port
    * type: number
    * desc: godon port
* api_version
    * flags: --api-version
    * type: string
    * desc: godon api version

> Show a breeder

~~~bash
set -eEux

__api_version="${api_version:-v0}"

curl --request GET \
     -H 'Content-Type: application/json' \
     --data "{ \"name\": \"${name}\" }" \
    "http://${hostname}:${port}/${__api_version}/breeders/${name}"
~~~
