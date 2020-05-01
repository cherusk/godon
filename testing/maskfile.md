# Godon Test Session Coordinator

## infra

> micro infrastructure stack related logic

### infra create

#### infra create machines (work_containment)

> Instanciate Micro Test Infra Stack machines based on kcli/libvirt

~~~bash
set -eEux

echo "instanciating machines"
kcli create \
     plan -f "${work_containment}/testing/infra/machines.yml" \
     micro_fedora_stack

kcli list plan
kcli list vm

~~~

#### infra create network (work_containment)

~~~bash
set -eEux

python "${work_containment}/testing/infra/network.py"
~~~

### infra cleanup 

#### infra cleanup machines

> Cleanup libvirt based test instances

~~~bash
set -eEux

kcli delete plan -y micro_fedora_stack
~~~

#### infra cleanup network 

> Cleanup mininet test network 

~~~bash
set -eEux

for switch in ovs_1 ovs_2 
do
    sudo ovs-vsctl del-br ${switch}
done

for link in ovs_1-eth1 ovs_2-eth1
do
    sudo ip link del ${link}
done

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
