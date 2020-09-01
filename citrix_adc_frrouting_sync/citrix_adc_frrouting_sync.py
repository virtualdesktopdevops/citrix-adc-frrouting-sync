#!/usr/bin/env python3

import citrix_adc_frrouting_sync.nitro as nitro
import os

class Sync():
  def __init__(self, url, username, password, nexthop):
    # start nitro client
    nitro_client = nitro.NitroClient(url, username, password)

    # disable ssl verification if needed
    nitro_client.set_verify("false")

    # Do the request to the NITRO API
    # Filter for VIP IP addresses to ignore SNIP and NSIP
    result = nitro_client.request(
        method='get',
        endpoint="config",
        objecttype="nsip",
        params="args=type:VIP"
    )

    try:
      #Check HTTP response code and parse only if result contains data.
      for vip in result.json()['nsip']:
        print(vip)
        # IF state = ENABLED & hostroute=ENABLED & vipvipvsrvrrhiactiveupcount > 0 => publish route
        if vip['state'] == 'ENABLED' and vip['hostroute'] == 'ENABLED':
          cmd = "vtysh -c 'configure terminal' -c 'ip route " + vip['ipaddress'] + " 255.255.255.255 " + nexthop +"'"
          os.system(cmd)
          print(cmd)
        # Else remove route. This method ensures that disabled VIP or unconfigured hostroutes are also removed from routing table
        else:
          cmd = "vtysh -c 'configure terminal' -c 'no ip route " + vip['ipaddress'] + " 255.255.255.255 " + nexthop +"'"
          os.system(cmd)
          print("Removing VIP "+ vip['ipaddress'] + " from routing table")
          print(cmd)

        # Make sure that no deleted VIP remains in frrouting by comparing static routes list with RHI enabled VIP list

    except:
      print('Unable to connect parse Virtual IP addresses in Nitro response')
      print(result.__dict__)
