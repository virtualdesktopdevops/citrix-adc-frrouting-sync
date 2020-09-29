#!/usr/bin/env python3

import unittest
from unittest import TestCase
import os
import time
import json
import pytest
import citrix_adc_frrouting.frrouting

@pytest.fixture(scope="module")
def citrix_adc_config():
    os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'enable ns feature LoadBalancing'")
    yield citrix_adc_config  # provide the fixture value
    print("Reset adc configuration")
    os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'rm lb vserver google_http_vsrv'")
    os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'rm service google_ssl_svc'")
    os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'rm ns ip 10.1.2.3'")
    

class TestSyncDaemon(TestCase):
    # Route shoud be advertised when a new lb vserverwith hostroute enabled is configured and goes up
    def test_add_citrix_adc_lb_vserver(self):
        os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'add ns ip 10.1.2.3 255.255.255.255 -type VIP -hostroute ENABLED'")
        os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'add service google_ssl_svc 216.58.206.227 SSL 443'")
        os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'add lb vserver google_http_vsrv HTTP 10.1.2.3 80'")
        os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'bind lb vserver google_http_vsrv google_ssl_svc'")
        time.sleep(5)
        frrclient = citrix_adc_frrouting.frrouting.FrroutingClient()
        static_routes = frrclient.get_routes_with_tag(99)
        assert list(static_routes)[0] == '10.1.2.3/32'

    # Route should be withdrawn when service goes up
    def test_disable_citrix_adc_service(self):
        os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'disable service google_ssl_svc'")
        time.sleep(10)
        frrclient = citrix_adc_frrouting.frrouting.FrroutingClient()
        static_routes = frrclient.get_routes_with_tag(99)
        self.assertFalse(static_routes)

    # Route should be advertised when service is up again
    def test_enable_citrix_adc_service(self):
        os.system("docker exec -i citrix-adc-frrouting-sync_cpx_130_1 cli_script.sh 'enable service google_ssl_svc'")
        time.sleep(10)
        frrclient = citrix_adc_frrouting.frrouting.FrroutingClient()
        static_routes = frrclient.get_routes_with_tag(99)
        assert list(static_routes)[0] == '10.1.2.3/32'

    # All routes have to be withdrawn if Citrix ADC goes down
    def test_stop_citrix_adc_cpx(self):
        os.system("docker-compose -f docker-compose.ci.yml down")
        time.sleep(10)
        frrclient = citrix_adc_frrouting.frrouting.FrroutingClient()
        static_routes = frrclient.get_routes_with_tag(99)
        self.assertFalse(static_routes)