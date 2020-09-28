#!/usr/bin/env python3

import unittest
from unittest import TestCase
import mock
import subprocess
import json
import citrix_adc_frrouting.frrouting

class TestGetStaticRoutes(TestCase):
    @mock.patch("subprocess.check_output", mock.MagicMock(return_value = bytes('{"10.1.2.3/32": [{"prefix": "10.1.2.3/32", "protocol": "static", "selected": "True", "destSelected": "True", "distance": 1, "metric": 0, "installed": "True", "tag": 99, "table": 254, "internalStatus": 16, "internalFlags": 72, "internalNextHopNum": 1, "internalNextHopActiveNum": 1, "uptime": "00:01:12", "nexthops": [{"flags": 3, "fib": "True", "ip": "172.18.160.1", "afi": "ipv4", "interfaceIndex": 4, "interfaceName": "eth0", "active": "True"}]}]}', 'utf-8')))
    def test_get_static_routes(self):
        frrclient = citrix_adc_frrouting.frrouting.FrroutingClient()
        static_routes = frrclient.get_static_routes()
        assert list(static_routes)[0] == '10.1.2.3/32'