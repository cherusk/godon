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
# Godon Test Session Coordinator

## config

> config generation auxiliary logic

### config generate

#### config generate prometheus

> config generator for prometheus monitored targets

~~~bash
set -eEux

__kcli_cmd="mask --maskfile ${MASKFILE_DIR}/maskfile.md util kcli run"

 ## generate prometheus target config
__target_ip_addresses_array=($(${__kcli_cmd} "list vm" | grep 'micro_stack' | awk -F\| '{ print $4 }' | xargs))

cat << EOF > targets.json

[
	{
		"targets": [
			"${__target_ip_addresses_array[0]}:8090"
		],
		"labels": {
			"job": "socket_statistics"
		}
	},
	{
		"targets": [
			"${__target_ip_addresses_array[1]}:8090"
		],
		"labels": {
			"job": "socket_statistics"
		}
	}
]

EOF

~~~

#### config generate breeder (output_file)

> config generator for breeder test run

~~~bash
set -eEux

__template_file="${MASKFILE_DIR}/../examples/network.yml"
__kcli_cmd="mask --maskfile ${MASKFILE_DIR}/maskfile.md util kcli run"

 ## generate breeder test run config from running instances
__target_ip_addresses_array=($(${__kcli_cmd} "list vm" | grep 'micro_stack' | awk -F\| '{ print $4 }' | xargs))


  ## empty existing targets
cat "${__template_file}" | yq '.breeder.effectuation.targets |= []'  | yq --yaml-output > ${output_file}

for __target_ip_address in ${__target_ip_addresses_array}
do
  targets_object="{ "user": "godon_robot", "key_file": "/opt/airflow/credentials/id_rsa", "address": "${__target_ip_address}" }"
  cat "${__template_file}" | yq '.breeder.effectuation.targets += $ENV.targets_object' | yq --yaml-output > ${output_file}
done

~~~



## infra

> micro infrastructure stack related logic

### infra create

#### infra create machines

> Instanciate Micro Test Infra Stack machines based on kcli/libvirt

~~~bash
set -eEux

__plan_name=micro_stack
__kcli_cmd="mask --maskfile ${MASKFILE_DIR}/maskfile.md util kcli run"

echo "instanciating machines"
${__kcli_cmd} "create plan -f ./infra/machines/plan.yml ${__plan_name}"

${__kcli_cmd} "list plan"
${__kcli_cmd} "list vm"

~~~

#### infra create network

> Errect micro test network

~~~bash
set -eEux

 # improvised since of mininet disarray and kcli work ongoing
 # create link between switches

link_instance_to_switch() {

    __instance="${1}"
    __switch="${2}"
    __port_name="${3}"

     # render libvirt to ovs link config
    __link_template="${MASKFILE_DIR}/infra/libvirt/network/ovs_link_template.xml"
    __link_definition="${MASKFILE_DIR}/infra/libvirt/network/ovs_link.xml"
    export __switch
    export __port_name
    envsubst < "${__link_template}" > "${__link_definition}"


    virsh attach-device --domain "${__instance}" \
                        --file "${__link_definition}" \
                        --persistent
}

ip link add veth_port_0 type veth peer name veth_port_1

for switch_number in $(seq 0 1)
do
    switch_name="switch_${switch_number}"

    # connect 
    ovs-vsctl add-br "${switch_name}"
    ovs-vsctl add-port "${switch_name}" "veth_port_${switch_number}"

    # activate
    ip link set "${switch_name}" up
    ip link set "veth_port_${switch_number}" up
done

tc qdisc add dev veth_port_0 root netem rate 10mbit delay 4ms

link_instance_to_switch "source_vm" "switch_0" "source_vm_port"
link_instance_to_switch "sink_vm" "switch_1" "sink_vm_port"

~~~

### infra cleanup

#### infra cleanup machines

> Cleanup libvirt based test instances

~~~bash
set -eEux

__kcli_cmd="mask --maskfile ${MASKFILE_DIR}/maskfile.md util kcli run"

${__kcli_cmd} "delete plan -y micro_stack"
~~~

#### infra cleanup network

> Cleanup micro test network

~~~bash
set -eEux


for switch_number in $(seq 0 1)
do
    switch_name="switch_${switch_number}"
    ovs-vsctl del-br "${switch_name}" || exit 0
done

ip link del veth_port_0 || exit 0

~~~

### infra provision

#### infra provision machines

> Provision Test Infra Machine Instances

~~~bash
set -eEux

__plan_name=micro_stack
__kcli_cmd="mask --maskfile ${MASKFILE_DIR}/maskfile.md util kcli run"

echo "provisioning infra instances"

~~~

## godon

> Mngnt logic for the godon stack 

### godon create

> Create godon services

~~~bash
set -eEux

docker-compose -f "${MASKFILE_DIR}/../docker-compose.yml" up -d

~~~

### godon cleanup

> Cleanup godon services

~~~bash
set -eEux

docker-compose -f "${MASKFILE_DIR}/../docker-compose.yml" down

~~~

## testing

### testing perform

> Perform/Orchestrate Session of Tests Run

~~~bash
set -eEux

echo "performing tests"

 # TODO improvised until formatted parser install 
target_ip="$(sudo ansible-inventory --list -y -i ${MASKFILE_DIR}/infra/inventory.sh | 
             grep ansible_host | head -n 1 | \
             awk -F: '{print $2}' | xargs echo -n)"
svc_name=control_loop
dag_name="lnx_net_stack"


sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" exec -T "${svc_name}" \
                        airflow variables --set target "${target_ip}"
sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" exec -T "${svc_name}" \
                        airflow trigger_dag "${dag_name}"

~~~

## util

> Test flow utilities 

### util kcli 

> kcli specific wrappers

#### util kcli run (cmd)

> kcli invocation wrapper 

~~~bash
set -eEux

container_name="quay.io/karmab/kcli:22.07"
pool_dir="/github-runner/artifacts/"

docker run --net host --rm \
           -t -a stdout -a stderr \
           -v ${pool_dir}:${pool_dir} \
           -v /var/run/libvirt:/var/run/libvirt \
           -v  ${MASKFILE_DIR}:/workdir \
           ${container_name} ${cmd}

~~~
