#!/bin/bash
# use "chmod +x ./filename.sh" to make file executable
# serial operate the commands

cd ../../..
ip link set enp1s0 mtu 9000 up &&
ip link set enp3s0 mtu 9000 up &&
ip addr add 10.38.1.3/16 dev enp1s0 &&
sleep 3
ip addr add 10.39.1.3/16 dev enp3s0 &&
source ~/mmwsdr/host/scripts/sivers_ftdi.sh