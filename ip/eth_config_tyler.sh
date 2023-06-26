ipaddr_2=$(ip -o -s -4 addr show enp94s0f0 | awk '{print $4}' | cut -d/ -f1 | cut -d. --fields 2)
ipaddr_3_4=$(ip -o -s -4 addr show enp94s0f0 | awk '{print $4}' | cut -d/ -f1 | cut -d. --fields 3,4)
echo $ipaddr_3_4
ifconfig eno1 10.$(($ipaddr_2 + 1)).$ipaddr_3_4 netmask 255.255.0.0 mtu 9000 up
ifconfig eno2 10.$(($ipaddr_2 + 2)).$ipaddr_3_4 netmask 255.255.0.0 mtu 9000 up
sysctl -w net.core.rmem_max=62500000
sysctl -w net.core.wmem_max=62500000
