#!/usr/bin/env python3

import os
from .nitro import NitroClient
from .frrouting import FrroutingClient

class SyncService():
  def __init__(self, url, username, password, nexthop):
    self.frr_client = FrroutingClient()
    self.nitro_client = NitroClient(url, username, password)
    # disable nitro client ssl verification
    self.nitro_client.set_verify("false")
    self.nexthop = nexthop
    self.nitro_url = url

  def start_sync(self):
    # Extract FRRouting configured hostroutes for ADC VIP
    frrouting_vip_routes_to_process = self.__get_frrouting_hostroutes(self.nexthop)
    print("Host routes already configured in FRRouting : " + str(frrouting_vip_routes_to_process))
    print("Beginning sync with Citrix ADC.")
    
    # Do the request to the NITRO API
    # Filter for VIP IP addresses to ignore SNIP and NSIP
    result = self.__get_adc_virtual_ipaddresses()

    #Check if result is a JSON containin a least one nsip object.
    if 'nsip' in result:
      orphaned_frrouting_routes = self.__sync_routes_with_active_virtual_ipaddresses(result, frrouting_vip_routes_to_process, self.nexthop)

      # Make sure that no deleted VIP remains in frrouting by removing all the static routes for VIP remaining in frrouting_vip_routes_to_process
      self.__remove_orphaned_hostroutes(orphaned_frrouting_routes, self.nexthop)
    else:
      print('ERROR : Unable to connect parse Virtual IP addresses in Nitro response')
      #print(result.__dict__)

  def __get_frrouting_hostroutes(self, nexthop):
    # Create an empty set on which all the frrouting configured VIP will be injected. 
    ipaddresses_set = set()
    
    # Create a list of prefixes matching for which configured nexthop matches nexthop parameter
    hostroutes = self.frr_client.get_routes_with_tag(99)
    for route in hostroutes:
          ipaddresses_set.add(route.split('/')[0])

    # Return ipaddresses_set unordered list of unique VIP.
    return ipaddresses_set

  def __get_adc_virtual_ipaddresses(self):
    try:
      return self.nitro_client.request(
          method='get',
          endpoint="config",
          objecttype="nsip",
          params="args=type:VIP"
      ).json()
    except:
      print("ERROR : Unable to connect to Citrix ADC NITRO API at " + self.nitro_url)
      exit()

  def __sync_routes_with_active_virtual_ipaddresses(self, virtual_ipaddresses, frrouting_vip_routes_to_process, nexthop):
    for vip in virtual_ipaddresses['nsip']:
        # IF state = ENABLED & hostroute=ENABLED & vipvipvsrvrrhiactiveupcount > 0 & route not already in routing table=> publish route
        if vip['state'] == 'ENABLED' and vip['hostroute'] == 'ENABLED' and vip['ipaddress'] not in frrouting_vip_routes_to_process:
          #Inject route using vtysh cli command
          print("Injecting new VIP "+ vip['ipaddress'] + " into routing table")
          self.frr_client.add_static_route_with_tag(vip['ipaddress'], "255.255.255.255", nexthop, 99)

        # IF state = ENABLED & hostroute=ENABLED & vipvipvsrvrrhiactiveupcount > 0 & route already in routing table=> do nothing
        elif vip['state'] == 'ENABLED' and vip['hostroute'] == 'ENABLED' and vip['ipaddress'] in frrouting_vip_routes_to_process:
          #Do nothing as configuration is ok and remove VIP from frrouting_vip_routes_to_process as it has been processed
          frrouting_vip_routes_to_process.remove(vip['ipaddress'])

        # Else remove route. This method ensures that disabled VIP or unconfigured hostroutes are also removed from routing table
        elif (vip['state'] == 'DISABLED' or vip['hostroute'] == 'DISABLED') and (vip['ipaddress'] in frrouting_vip_routes_to_process):
          #Remove route using vtysh cli command
          print("Removing down/disabled VIP "+ vip['ipaddress'] + " from routing table")
          self.frr_client.remove_static_route(vip['ipaddress'], "255.255.255.255", nexthop)
          #Remove VIP from frrouting_vip_routes_to_process as it has been processed
          frrouting_vip_routes_to_process.remove(vip['ipaddress'])

    #Return the list of VIP for which a route still exists in frrouting routing table
    #All the existing VIP in Citrix ADC (active or inactive) have been removed from this list
    return frrouting_vip_routes_to_process

  def __remove_orphaned_hostroutes(self, ip_addresses_dict, nexthop):
    for ip_address in ip_addresses_dict:
      print("Removing deleted VIP "+ ip_address + " from routing table")
      self.frr_client.remove_static_route(ip_address, "255.255.255.255", nexthop)

    

