#!/usr/bin/env bash

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
