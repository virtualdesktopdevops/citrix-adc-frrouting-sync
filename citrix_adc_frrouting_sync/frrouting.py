#!/usr/bin/env python3

"""frrouting.py: Python class to configure with FRROUTING"""

import requests
import subprocess
import os
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
            os.system(cmd , shell=True)
            return True
        except:
            return False

    def get_static_routes(self):
        return self.__exec_show_command("show ip route static json")
    
    def get_routes_with_tag(self, tag):
        return self.__exec_show_command("show ip route tag " + str(tag) + " json")
    