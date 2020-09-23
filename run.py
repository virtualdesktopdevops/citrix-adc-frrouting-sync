#!/usr/bin/env python3

import configparser
import sys
import getopt
import os
import daemon
import argparse
import logging
import time
import citrix_adc_frrouting.sync
from daemon import pidfile

debug_enabled = False

# folder where script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main(config: dict, log_file: str, daemon: bool ):
    # Configure logging
    logger = logging.getLogger('eg_daemon')
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(formatstr)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Run sync
    if config.has_option('ADC', 'NITRO_URL') and config.has_option('ADC', 'PASSWORD') and config.has_option('ADC', 'LOGIN') and config.has_option('ADC', 'CONTAINER_IP_ADDRESS'):
        sync_engine = citrix_adc_frrouting.sync.SyncService(
            config['ADC']['NITRO_URL'], 
            config['ADC']['LOGIN'], 
            config['ADC']['PASSWORD'], 
            config['ADC']['CONTAINER_IP_ADDRESS'])

        if daemon:
            logger.info("Initializing periodic sync every 5 seconds as daemon")
            while True:
                logger.info("Beginning sync")
                sync_engine.start_sync()
                logger.info("End of sync")
                time.sleep(5)  
        else:
            sync_engine.start_sync()
              
    else:
        print('Missing at least one of the NITRO_URL, LOGIN, or PASSWORD configuration parameters')
        logger.error('Missing at least one of the NITRO_URL, LOGIN, or PASSWORD configuration parameters')

def start_daemon(pid_file: str, log_file: str, config: dict):
    """
    Function launches  daemon in its context
    :param pid_file:
    :type str:
    :param log_file:
    :type str:
    """

    global debug_enabled

    if debug_enabled:
        print('citrixadcfrroutingsync_daemon: pid file {}'.format(pid_file))
        print('citrixadcfrroutingsync: log file {}'.format(log_file))
        print('citrixadcfrroutingsync: about to start daemonization')

    # pidfile is a context
    with daemon.DaemonContext(
            working_directory=BASE_DIR,
            umask=0o002,
            pidfile=pidfile.TimeoutPIDLockFile(pid_file),
    ) as context:
        main(config, log_file, True)

if __name__ == "__main__":
    configfile = ''

    parser = argparse.ArgumentParser(description='Newapi daemon in Python')
    parser.add_argument('-c', '--config', help='INI configuration file name')
    parser.add_argument('-d', '--daemonize', action='store_true', default=False, help='Daemonize sync process')
    parser.add_argument('-p', '--pid-file', default='/var/run/citrixadcfrroutingsync.pid', help='absolute pid file name')
    parser.add_argument('-l', '--log-file', default='/var/log/citrixadcfrroutingsync.log', help='absolute log file name')

    args = parser.parse_args()

    # Read configuration file
    config = configparser.ConfigParser()
    config.read(args.config)

    if args.daemonize:
        start_daemon(pid_file=args.pid_file, log_file=args.log_file, config=config)
    else:        
        main(config, args.log_file, False)
