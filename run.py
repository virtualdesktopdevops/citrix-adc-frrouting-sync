#!/usr/bin/env python3

import configparser
import sys
import getopt
import citrix_adc_frrouting.sync

def main(argv):
    configfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["config="])
    except getopt.GetoptError:
        print('run.py --config <configfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('run.py --config <configfile>')
            sys.exit()
        elif opt in ("-c", "--config"):
            configfile = arg

    # Read configuration file
    config = configparser.ConfigParser()
    config.read(configfile)

    # Run sync
    if config.has_option('ADC', 'NITRO_URL') and config.has_option('ADC', 'PASSWORD') and config.has_option('ADC', 'LOGIN') and config.has_option('ADC', 'CONTAINER_IP_ADDRESS'):
        sync_engine = citrix_adc_frrouting.sync.SyncService(
            config['ADC']['NITRO_URL'], 
            config['ADC']['LOGIN'], 
            config['ADC']['PASSWORD'], 
            config['ADC']['CONTAINER_IP_ADDRESS'])
        sync_engine.start_sync()
    else:
        print('Missing at least one of the NITRO_URL, LOGIN, or PASSWORD configuration parameters')

if __name__ == "__main__":
    main(sys.argv[1:])
