#!/usr/bin/env python3

import configparser
from citrix_adc_frrouting_sync import citrix_adc_frrouting_sync

# Read local file `config.ini`.
config = configparser.ConfigParser()
config.read('conf/config.ini')

# Run a test server.
citrix_adc_frrouting_sync.Sync(config['ADC']['NITRO_URL'], config['ADC']['LOGIN'], config['ADC']['PASSWORD'])