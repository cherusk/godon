#!/usr/bin/env bash

set -Eeu

__machine="${1}"
__ovs_link="ens7"

if [[ "${__machine}" == "source_vm" ]]; then
    __ovs_net_address="10.0.6.5/24"
elif [[ "${__machine}" == "sink_vm" ]]; then
    __ovs_net_address="10.0.6.6/24"
else
    echo "unknown machine to configure: ${__machine}"
    exit 1
fi

ip addr add "${__ovs_net_address}" dev "${__ovs_link}"
ip link set dev "${__ovs_link}" up
