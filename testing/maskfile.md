# Godon Test Run Coordinator

## instanciate

> Instanciate Test Infra Stack with help of kcli on local libvirtd

~~~sh

set -eEux

echo "instanciating infra"

kcli create plan -f "${SOFT_RESIDE}/infra/machines.yml" micro_fedora
kcli list image

sleep 1

kcli list plan
kcli list vm

~~~

## provision

> Provision Test Infra Instances

~~~sh

set -eEux

echo "provisioning infra"
# ansible to come
~~~

## perform

> Perform/Orchestrate Run of Tests 

~~~sh

set -eEux

echo "performing tests"
# ansible to come
~~~
