# Godon Test Session Coordinator

## infra

> micro infrastructure stack related logic

### infra create

#### infra create machines

> Instanciate Micro Test Infra Stack machines based on kcli/libvirt

~~~bash
set -eEux

__plan_name=micro_stack

echo "instanciating machines"
sudo kcli create \
     plan -f "${MASKFILE_DIR}/infra/machines.yml" \
     "${__plan_name}"

sudo kcli list plan
sudo kcli list vm

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
    __link_template="${MASKFILE_DIR}/infra/network/libvirt_ovs_link_template.xml"
    __link_definition="${MASKFILE_DIR}/infra/network/libvirt_ovs_link.xml"
    export __switch
    export __port_name
    envsubst < "${__link_template}" > "${__link_definition}"


    sudo virsh attach-device --domain "${__instance}" \
                             --file "${__link_definition}" \
                             --persistent
}

sudo ip link add veth_port_0 type veth peer name veth_port_1

for switch_number in $(seq 0 1)
do
    switch_name="switch_${switch_number}"

    # connect 
    sudo ovs-vsctl add-br "${switch_name}"
    sudo ovs-vsctl add-port "${switch_name}" "veth_port_${switch_number}"

    # activate
    sudo ip link set "${switch_name}" up
    sudo ip link set "veth_port_${switch_number}" up
done

sudo tc qdisc add dev veth_port_0 root netem rate 10mbit delay 4ms

link_instance_to_switch "source_vm" "switch_0" "source_vm_port"
link_instance_to_switch "sink_vm" "switch_1" "sink_vm_port"

~~~

### infra cleanup

#### infra cleanup machines

> Cleanup libvirt based test instances

~~~bash
set -eEux

sudo kcli delete plan -y micro_stack
~~~

#### infra cleanup network

> Cleanup micro test network

~~~bash
set -eEux


for switch_number in $(seq 0 1)
do
    switch_name="switch_${switch_number}"
    sudo ovs-vsctl del-br "${switch_name}" || exit 0
done

sudo ip link del veth_port_0 || exit 0

~~~

### infra provision

#### infra provision machines

> Provision Test Infra Machine Instances

~~~bash
set -eEux

__plan_name=micro_stack

echo "provisioning infra instances"

__credentials_dir="${MASKFILE_DIR}/infra/credentials/ssh/"

chmod -R 0400 "${__credentials_dir}/id_rsa"

__sentinel=0
until sudo ansible-inventory -i /usr/bin/klist.py --list | grep -q ansible_host
do
    echo "awaiting libvirt instances init completion"
    sudo kcli list vm > /dev/null
    sleep 30
    if [[ "${__sentinel}" > 6 ]]
    then
        sudo kcli restart plan "${__plan_name}"
    fi
    ((__sentinel++)) || true
done

sudo -E ansible-playbook --private-key "${__credentials_dir}/id_rsa" \
                         --user root \
                         --become \
                         -i "/usr/bin/klist.py" \
                         -T 30 \
                         --ssh-extra-args="-o StrictHostKeyChecking=no" \
                         "${MASKFILE_DIR}/infra/provisioning/perform.yml"

~~~

## godon

> Mngnt logic for the godon stack 

### godon setup 

> Errect the parts of godon

~~~bash
set -eEux

svc_name=control_loop

sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" up -d

sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" exec -T --user root "${svc_name}" \
                       chown -R airflow:airflow /opt/airflow/credentials/

~~~

### godon deplete 

> Deplete parts of godon

~~~bash
set -eEux

sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" down 

~~~

## testing

### testing perform

> Perform/Orchestrate Session of Tests Run

~~~bash
set -eEux

echo "performing tests"

 # TODO improvised until formatted parser install 
target_ip="$(sudo ansible-inventory -i /usr/bin/klist.py --list --yaml | 
             grep ansible_host | head -n 1 | \
             awk -F: '{print $2}' | xargs echo -n)"
svc_name=control_loop
dag_name="lnx_net_stack"


sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" exec -T "${svc_name}" \
                        airflow variables --set target "${target_ip}"
sudo docker-compose -f "${MASKFILE_DIR}/docker-compose.yml" exec -T "${svc_name}" \
                        airflow trigger_dag "${dag_name}"

~~~
