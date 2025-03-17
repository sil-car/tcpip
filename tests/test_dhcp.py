import unittest
from network_simulator import components
from network_simulator import dhcp
from network_simulator import errors


class TestDhcp(unittest.TestCase):
    def setUp(self):
        self.net = '192.168.1.0/24'
        self.gw = '192.168.1.1'
        dhcpsrv = dhcp.Server('192.168.1.20', '192.168.1.250')
        self.n0 = components.Eth(address=self.gw, dhcp=dhcpsrv, gateway=self.gw, network=self.net)
        self.n1 = components.Eth()

    def test_add_lease1(self):
        self.n1.add_link(self.n0)
        self.assertEqual(str(self.n1.ip4_address), '192.168.1.20')
    
    def test_add_lease_full(self):
        ip = self.n0.dhcp.start
        while ip <= self.n0.dhcp.end:
            n = components.Eth()
            n.add_link(self.n0)
            ip += 1
        nic = components.Eth()
        self.assertRaises(errors.DuplicateDhcpAddress, nic.add_link, self.n0)
    
    def test_remove_lease(self):
        self.n1.add_link(self.n0)
        ip = self.n1.ip4_address
        self.n1.remove_link(self.n0)
        self.n0.dhcp.remove_lease(ip)
        self.assertEqual(0, len(self.n0.dhcp.leases))
