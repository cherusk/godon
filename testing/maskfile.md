# Godon Test Session Coordinator

## infra

> micro infrastructure stack related logic

### infra create

#### infra create machines

> Instanciate Micro Test Infra Stack machines based on kcli/libvirt

~~~bash
set -eEux

echo "instanciating machines"
sudo kcli create \
     plan -f "${MASKFILE_DIR}/infra/machines.yml" \
     micro_fedora_stack

kcli list plan
kcli list vm

~~~

#### infra create network

> Errect micro test network

~~~bash
set -eEux

 # improvised since of mininet disarray and kcli work ongoing
 # create link between switches
sudo ip link add veth_port_0 type veth peer name veth_port_1

for switch_number in $(seq 0 1)
do
    switch_name="switch_${switch_number}"
    sudo ovs-vsctl add-br "${switch_name}"
    sudo ovs-vsctl add-port "${switch_name}" "veth_port_${switch_number}"
done

tc qdisc add dev veth_port_0 root netem rate 10mbit delay 4ms

~~~

### infra cleanup

#### infra cleanup machines

> Cleanup libvirt based test instances

~~~bash
set -eEux

sudo kcli delete plan -y micro_fedora_stack
~~~

#### infra cleanup network

> Cleanup micro test network

~~~bash
set -eEux


for switch_number in $(seq 0 1)
do
    switch_name="switch_${switch_number}"
    sudo ovs-vsctl del-br "${switch_name}"
done

sudo ip link del veth_port_0

~~~

### infra provision

#### infra provision machines

> Provision Test Infra Machine Instances

~~~bash
set -eEux

echo "provisioning infra instances"

~~~

## testing

### testing perform

> Perform/Orchestrate Session of Tests Run

~~~bash
set -eEux

echo "performing tests"

~~~
