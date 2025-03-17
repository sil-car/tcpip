import unittest
from network_simulator import components
from network_simulator import constants
from network_simulator import ping


class TestPingGateway(unittest.TestCase):
    def setUp(self):
        self.net = '192.168.1.0/24'
        self.gw = '192.168.1.1'
        self.n0 = components.Eth(address=self.gw, gateway=self.gw, network=self.net)

    def test_ping_to_gateway_eth(self):
        nic = components.Eth(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic.add_link(self.n0)

        p = ping.ping(nic, '192.168.1.1')
        t = constants.COPPER_LATENCY
        self.assertAlmostEqual(p, t, 1)

    def test_ping_to_gateway_optical(self):
        nic = components.Opt(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic.add_link(self.n0)

        p = ping.ping(nic, '192.168.1.1')
        t = constants.FIBER_LATENCY
        self.assertAlmostEqual(p, t, 1)

    def test_ping_to_gateway_wifi(self):
        nic = components.Wifi(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic.add_link(self.n0)

        p = ping.ping(nic, '192.168.1.1')
        t = constants.WIFI_LATENCY
        self.assertAlmostEqual(p, t, 1)


class TestPingLocal(unittest.TestCase):
    def setUp(self):
        self.net = '192.168.1.0/24'
        self.gw = '192.168.1.1'
        self.nic0 = components.Eth(address=self.gw, gateway=self.gw, network=self.net)
        self.dest_ip = '192.168.1.3'

    def test_ping_to_lan_eth_eth(self):
        nic2 = components.Eth(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic3 = components.Eth(address=self.dest_ip, gateway=self.gw, network=self.net)
        nic2.add_link(self.nic0)
        nic3.add_link(self.nic0)

        p = ping.ping(nic2, self.dest_ip)
        t = constants.COPPER_LATENCY * 2
        self.assertAlmostEqual(p, t, 1)

    def test_ping_to_lan_eth_wifi(self):
        nic2 = components.Eth(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic3 = components.Wifi(address=self.dest_ip, gateway=self.gw, network=self.net)
        nic2.add_link(self.nic0)
        nic3.add_link(self.nic0)

        p = ping.ping(nic2, self.dest_ip)
        t = constants.COPPER_LATENCY + constants.WIFI_LATENCY
        self.assertAlmostEqual(p, t, 1)

    def test_ping_to_lan_wifi_wifi(self):
        nic2 = components.Wifi(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic3 = components.Wifi(address=self.dest_ip, gateway=self.gw, network=self.net)
        nic2.add_link(self.nic0)
        nic3.add_link(self.nic0)

        p = ping.ping(nic2, self.dest_ip)
        t = constants.WIFI_LATENCY * 2
        self.assertAlmostEqual(p, t, 1)

    def test_ping_to_lan_via_intermediate_router(self):
        # Topology: nic2 > router4 > nic0 (gateway) > nic3
        nic2 = components.Eth(address='192.168.1.2', gateway=self.gw, network=self.net)
        nic3 = components.Eth(address=self.dest_ip, gateway=self.gw, network=self.net)
        nic3.add_link(self.nic0)
        router4 = components.Eth(address='192.168.1.4', gateway=self.gw, network=self.net)
        router4.add_link(self.nic0)
        nic2.add_link(router4)

        p = ping.ping(nic2, self.dest_ip)
        t = constants.COPPER_LATENCY * 3
        self.assertAlmostEqual(p, t, 1)


class TestPingPublic(unittest.TestCase):
    def setUp(self):
        self.net = '192.168.1.0/24'
        self.gw = '192.168.1.1'
        self.nic0 = components.Eth(address=self.gw, gateway=self.gw, network=self.net)
        self.dest_ip = '1.1.1.1'
        self.nic1 = components.Public(address=self.dest_ip)

    def test_ping_gateway_to_public(self):
        self.nic0.add_link(self.nic1)
        p = ping.ping(self.nic0, self.dest_ip)
        t = constants.FIBER_LATENCY
        self.assertAlmostEqual(p, t, 1)