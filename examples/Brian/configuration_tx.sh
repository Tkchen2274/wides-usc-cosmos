#!/bin/bash
# use "chmod +x ./filename.sh" to make file executable
# serial operate the commands

cd ~
ifconfig data1 10.38.1.3 netmask 255.255.0.0 mtu 9000 up &&
sleep 1
sysctl -w net.core.wmem_max=62500000 &&
sleep 0.5
sysctl -w net.core.rmem_max=62500000