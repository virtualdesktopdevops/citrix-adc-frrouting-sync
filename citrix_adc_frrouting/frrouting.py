#!/usr/bin/env python3

"""frrouting.py: Python class to configure FRROUTING with vtysh shell utility"""

import subprocess
import json

class FrroutingClient():
    def __init__(self):
        pass

    def __exec_show_command(self, show_cmd):
        cmd = "vtysh -c '" + show_cmd +"'"
        raw_vtysh_data = subprocess.check_output(cmd , shell=True)
        return json.loads(raw_vtysh_data.decode('utf-8'))
  
    def __exec_config_command(self, config_cmd):
        cmd = "vtysh -c 'configure terminal' -c '" + config_cmd +"'"
        try:
            output = subprocess.check_output(cmd , shell=True)
            print(cmd)
            return True
        except:
            print("ERROR during "+ cmd + " execution")
            return False

    def get_static_routes(self):
        return self.__exec_show_command("show ip route static json")
    
    def get_routes_with_tag(self, tag):
        return self.__exec_show_command("show ip route tag " + str(tag) + " json")

    def add_static_route_with_tag(self, ip_address, netmask, nexthop, tag):
        self.__exec_config_command("ip route " + ip_address + " "+ netmask + " "+ nexthop + " tag " + str(tag))

    def remove_static_route(self, ip_address, netmask, nexthop):
        self.__exec_config_command("no ip route " + ip_address + " "+ netmask + " " + nexthop)
    