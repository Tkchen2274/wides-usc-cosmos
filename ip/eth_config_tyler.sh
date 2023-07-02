ipaddr_2=$(ip -o -s -4 addr show enp134s0 | awk '{print $4}' | cut -d/ -f1 | cut -d. --fields 2)
# gets the second octet of the ipv4 address. stores into the ipaddr_2 file
# X.Y.Z.W ~ gets the Y component
#
# maybe change show to enp134s0
ipaddr_3_4=$(ip -o -s -4 addr show enp94s0f0 | awk '{print $4}' | cut -d/ -f1 | cut -d. --fields 3,4)
# gets the third and fourth octet of ipv4 address. stores into the ipaaddr_3_4 aparts
# x.y.z.w ~ gets the z and w components
echo $ipaddr_3_4
# prints out the ipaddr_3_4 variable
ifconfig eno1 10.$(($ipaddr_2 + 1)).$ipaddr_3_4 netmask 255.255.0.0 mtu 9000 up
# if ipaddr_2 = y
# if ipaddr_3_4 = z.w
# then it's constructing 10.y.z.w
# ifconfig eno1 10.y.z.w netmask 255.255.0.0 mtu 9000 up 
# mtu sets the maximum transmission unit to 9000 bytes
# up brins the eno1 interface with enable network connectivity
# netmask: determine which part of an IP address represents the network portion and which part represents the host portion
ifconfig eno2 10.$(($ipaddr_2 + 2)).$ipaddr_3_4 netmask 255.255.0.0 mtu 9000 up
sysctl -w net.core.rmem_max=62500000
# Sets the max revieve socket buffer size to # bytes
sysctl -w net.core.wmem_max=62500000
# sets the max send socket buffer size to # bytes
