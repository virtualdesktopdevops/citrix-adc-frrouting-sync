# Citrix ADC FRROUTING SYNC
Python application to advertise RHI enabled Citrix ADC CPX & BLX virtual IP addresses in the network using [FRRouting](https://frrouting.org/) linux routing stack.

Citrix ADC activates VIP depending on the virtual server health (load-balancing, content-switching, ...). Frrouting handles peering with network peers using dynamic routing protocols as well as host routes redistribution in the datacenter network.

## Advertising host routes
Citrix ADC VIP with `-hostroute` parameter set to `ENABLED` are injected as static routes in FRRouting. Citrix ADC CPX docker private IP address, belonging to the docker network on which the CPX docker instance is running, is configured as nexthop of the static route.

Route tagging is used to further identify the Citrix ADC hostroutes and configure static route redistribution to BGP peers.

```
cmd = "vtysh -c 'configure terminal' -c 'ip route " + vip['ipaddress'] + " 255.255.255.255 " + nexthop +" tag 99'"
os.system(cmd)
```

## Pre-requisites 
  - Python 3.5+ environment.
  - Citrix ADC CPX 13.0
  - FRRouting
  - Root permissions required to allow the sync script to configure frrouting

## Installation
Install script should be run with root privileges to install python3 dependencies for root user.
```
pip3 install -r requirements.txt
pip3 install .
```


## Usage
### Install and configure FRRouting
#### Debian / Ubuntu
```
# add GPG key
curl -s https://deb.frrouting.org/frr/keys.asc | sudo apt-key add -

# possible values for FRRVER: frr-6 frr-7 frr-stable
# frr-stable will be the latest official stable release
FRRVER="frr-stable"
echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) $FRRVER | sudo tee -a /etc/apt/sources.list.d/frr.list

# update and install FRR
sudo apt update && sudo apt install frr frr-pythontools
```

#### Redhat / CentOS
```
# possible values for FRRVER: frr-6 frr-7 frr-stable
# frr-stable will be the latest official stable release
FRRVER="frr-stable"

# add RPM repository on CentOS 6
curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el6.noarch.rpm
sudo yum install ./$FRRVER*

# add RPM repository on CentOS 7
curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el7.noarch.rpm
sudo yum install ./$FRRVER*

# add RPM repository on CentOS 8
curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el8.noarch.rpm
sudo yum install ./$FRRVER*

# install FRR
sudo yum install frr frr-pythontools
```

### Deploy Citrix ADC CPX
#### Deploy Citrix ADC CPX using docker-compose
The following `docker-compose.yml` files deploys a pair of Citrix ADC CPX containers :
  - In a docker network with a fixed IP address to allow static routes configuration from the host to the container. Host mode is not used to make the deployment compatible with cloud virtual machines having a single network interface.
  - With least privileges, providing required `NET_ADMIN` permissions to the container, but running it as a non-root user.
  - Persisting the `/cpx` directory containing the Citrix ADC configuration files with a docker volume.

**Both CPX instances have to be deployed on 2 different physical or virtual hosts for effective resiliency. IP anycast is not needed if they are deployed on the same host as they are deployed on the same L3 subnet : unicast VIP in the L3 subnet is enough.**

IP Anycast is required when CPX HA pair is deployed on physical or virtual hosts being on disjoint L3 subnets.

_First ADC instance deployed on host 192.168.1.10/24_ :

`HOST: 192.168.1.10` environment variable is configured with the IP address of the docker host.

```
version: '3'

services:
  cpx_130:
    image: store/citrix/citrixadccpx:13.0-36.29
    ports:
      - 443:443/tcp
      - 80:80/tcp
      - 161:161/udp
      - 9080:9080/tcp
      - 9443:9443/tcp
      - 3003:3003/udp
      - 3008:3008/tcp
      - 8873:8873/tcp
    tty: true
    cap_add:
      - NET_ADMIN
    ulimits:
      core: -1
    volumes:
      - ./cpx:/cpx
    environment:
      EULA: 'yes'
      PLATFORM: 'CP1000'
      HOST: 192.168.1.10
    networks:
      cpx_net:
        ipv4_address: 172.18.0.254

networks:
  cpx_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/16

```

_Second ADC instance deployed on host 192.168.20.10/24_ :

`HOST: 192.168.20.10` environment variable is configured with the IP address of the docker host.

```
version: '3'

services:
  cpx_130:
    image: store/citrix/citrixadccpx:13.0-36.29
    ports:
      - 4433:443/tcp
      - 8080:80/tcp
      - 162:161/udp
      - 9081:9080/tcp
      - 9444:9443/tcp
      - 3004:3003/udp
      - 3009:3008/tcp
      - 8874:8873/tcp
    tty: true
    cap_add:
      - NET_ADMIN
    ulimits:
      core: -1
    volumes:
      - ./cpx:/cpx
    environment:
      EULA: 'yes'
      PLATFORM: 'CP1000'
      HOST: 192.168.20.10
    networks:
      cpx_net:
        ipv4_address: 172.18.0.253

networks:
  cpx_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/16

```

Then start the platform with `docker-compose up -d` on both docker hosts.

#### Configure a Citrix ADC CPX HA pair
Use the `docker exec -i <CPX node name> cli_script.sh 'add ha node 1 <remote node IP> [-inc enabled]'` command on each CPX node to configure the CPX HA pair.

With Citrix ADC CPX 13.0-64.35 release, CPX generates a random password for 'nsroot' user. After successful creation of CPX HA pair, the cli_script.sh on secondary node requires credentials as 2nd argument while cli_script.sh on primary CPX will work seamlessly unless the password is changed manually.

The password is saved in /var/deviceinfo/random_id file on CPX's file system. cli_script.sh automatically reads the password from this file. If you are changing the password, then cli_script.sh will take credentials as 2nd argument. 

Here's how we can provide the password to cli_script.sh : 
```
cli_script.sh "<command>" ":<user>:<password>"
```

Example :
```
cli_script.sh "show ns ip" ":nsroot:Citrix123"
```

#### Configure load-balancing virtual server
Connect into the primary Citrix ADC CPX container using `docker exec -i citrixadcfrroutingsync_cpx_130_1 /bin/bash`command and configure the load-balancing virtual server and service :

```
cli_script.sh 'add service google_ssl_svc 216.58.206.227 SSL 443'
cli_script.sh 'add lb vserver google_http_vsrv HTTP 10.1.2.3 80'
cli_script.sh 'bind lb vserver google_http_vsrv google_ssl_svc'
   
```

#### Enable route health injection for the virtual server
 The `hostroute ENABLED` parameter of a Citrix ADC virtual IP is used to enable route health injection on a specific virtual IP.

```
cli_script.sh 'set ns ip 10.1.2.3 -hostroute ENABLED'
```


### Start Citrix ADC Frrouting Sync daemon
Create a config.ini containing deployment parameters :

```
[ADC]
NITRO_URL = http://localhost:9080
CONTAINER_IP_ADDRESS = 172.18.0.254
LOGIN = nsroot
PASSWORD = nsroot
MODE = CPX
```

Run the synchronisation daemon **on both hosts running a member of the CPX HA pair** using the following command :

```
sudo ./run.py --config sample-config/config.ini -d
```

### Logging
Default Citrix ADC Frrouting sync log file is `/var/log/citrixadcfrroutingsync.log`. Log file can be changed using the `--log-file` cli parameter at deamon startup. 

