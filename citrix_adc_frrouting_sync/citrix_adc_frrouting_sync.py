#!/usr/bin/env python3

import citrix_adc_frrouting_sync.nitro as nitro
import citrix_adc_frrouting_sync.frrouting as frrouting
import os

class Sync():
  def __init__(self, url, username, password, nexthop):
    # Extract FRRouting configured hostroutes for ADC VIP
    frrouting_vip_routes_to_process = self.get_frrouting_hostroutes(nexthop)
    print("Host routes already configured in FRRouting : " + str(frrouting_vip_routes_to_process))
    print("Beginning sync with Citrix ADC.")

    # start nitro client
    nitro_client = nitro.NitroClient(url, username, password)

    # disable ssl verification if needed
    nitro_client.set_verify("false")

    # Do the request to the NITRO API
    # Filter for VIP IP addresses to ignore SNIP and NSIP
    try:
      result = nitro_client.request(
          method='get',
          endpoint="config",
          objecttype="nsip",
          params="args=type:VIP"
      ).json()
    except:
      print("ERROR : Unable to connect to Citrix ADC NITRO API at " + url)
      exit()

    if 'nsip' in result:
      #Check HTTP response code and parse only if result contains data.
      for vip in result['nsip']:
        # IF state = ENABLED & hostroute=ENABLED & vipvipvsrvrrhiactiveupcount > 0 & route not already in routing table=> publish route
        if vip['state'] == 'ENABLED' and vip['hostroute'] == 'ENABLED' and vip['ipaddress'] not in frrouting_vip_routes_to_process:
          #Inject route using vtysh cli command
          cmd = "vtysh -c 'configure terminal' -c 'ip route " + vip['ipaddress'] + " 255.255.255.255 " + nexthop +" tag 99'"
          os.system(cmd)
          print("Injecting new VIP "+ vip['ipaddress'] + " into routing table")
          print(cmd)

        # IF state = ENABLED & hostroute=ENABLED & vipvipvsrvrrhiactiveupcount > 0 & route already in routing table=> do nothing
        elif vip['state'] == 'ENABLED' and vip['hostroute'] == 'ENABLED' and vip['ipaddress'] in frrouting_vip_routes_to_process:
          #Do nothing as configuration is ok and remove VIP from frrouting_vip_routes_to_process as it has been processed
          frrouting_vip_routes_to_process.remove(vip['ipaddress'])

        # Else remove route. This method ensures that disabled VIP or unconfigured hostroutes are also removed from routing table
        elif (vip['state'] == 'DISABLED' or vip['hostroute'] == 'DISABLED') and (vip['ipaddress'] in frrouting_vip_routes_to_process):
          #Remove route using vtysh cli command
          cmd = "vtysh -c 'configure terminal' -c 'no ip route " + vip['ipaddress'] + " 255.255.255.255 " + nexthop +"'"
          os.system(cmd)
          print("Removing down/disabled VIP "+ vip['ipaddress'] + " from routing table")
          print(cmd)
          #Remove VIP from frrouting_vip_routes_to_process as it has been processed
          frrouting_vip_routes_to_process.remove(vip['ipaddress'])

      # Make sure that no deleted VIP remains in frrouting by removing all the static routes for VIP remaining in frrouting_vip_routes_to_process
      for ip_address in frrouting_vip_routes_to_process:
        cmd = "vtysh -c 'configure terminal' -c 'no ip route " + ip_address + " 255.255.255.255 " + nexthop +"'"
        os.system(cmd)
        print("Removing deleted VIP "+ ip_address + " from routing table")
        print(cmd)
    else:
      print('ERROR : Unable to connect parse Virtual IP addresses in Nitro response')
      #print(result.__dict__)

  def get_frrouting_hostroutes(self, nexthop):
    # Create an empty set on which all the frrouting configured VIP will be injected. 
    ipaddresses_set = set()

    # Extract currently configured static routes from FRROUTING
    frr_client = frrouting.FrroutingClient()
    
    # Create a list of prefixes matching for which configured nexthop matches nexthop parameter
    hostroutes = frr_client.get_routes_with_tag(99)
    for route in hostroutes:
          ipaddresses_set.add(route.split('/')[0])

    # Return ipaddresses_set unordered list of unique VIP.
    return ipaddresses_set
    

