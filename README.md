# Citrix ADC FRROUTING SYNC
Python application to advertise RHI enabled Citrix ADC CPX & BLX virtual IP addresses in the network using FRROUTING linux routing stack.

Citrix ADC activates VIP depending on the virtual server health (load-balancing, content-switching, ...), frrouting handles peering with network peers using dynamic routing protocols as well as host routes redistribution in the datacenter network.

## Advertising host routes
Citrix ADC VIP with hostroute parameter set to ENABLED are injected as static routes in FRRouting. Citrix ADC CPX docker private IP address, belonging to the docker network on which the CPX docker instance in running is configured as nexthop of the static route.

Route tagging is used to further quickly identify the Citrix ADC hostroutes and configure static route redistribution to BGP peers.

```
cmd = "vtysh -c 'configure terminal' -c 'ip route " + vip['ipaddress'] + " 255.255.255.255 " + nexthop +" tag 99'"
os.system(cmd)
```


## Requirements 
Python 3 environment.