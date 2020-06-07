#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import TCLink
from mininet.log import info, setLogLevel

setLogLevel('info')

net = Mininet(controller=Controller)

info('*** Adding switches\n')
ovs_1 = net.addSwitch('ovs_1')
ovs_2 = net.addSwitch('ovs_2')

info('*** Creating emulation link\n')
net.addLink(ovs_1, ovs_2,
            cls=TCLink, delay='2ms', bw=1000)

info('*** Starting network\n')
net.start()
