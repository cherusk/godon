#!/usr/bin/env bash
##
## Copyright (c) 2019 Matthias Tafelmeier.
##
## This file is part of godon
##
## godon is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## godon is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this godon. If not, see <http://www.gnu.org/licenses/>.
##

set -eEux

__repo_id=prometheus_ss_exporter
__repo_url="https://github.com/cherusk/${__repo_id}.git"
__tempdir="$(mktemp -d)"

pushd "${__tempdir}" 
git clone "${__repo_url}"
cd "${__repo_id}"
python3 setup.py install
popd

# cleanup
rm -r "${__tempdir}"
