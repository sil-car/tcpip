import ipaddress
from .errors import DuplicateDhcpAddress


class Server:
    def __init__(self, start=None, end=None):
        self.start = None
        self.end = None
        if start:
            if not isinstance(start, ipaddress.IPv4Address):
                start = ipaddress.ip_address(start)
            self.start = start
        if end:
            if not isinstance(end, ipaddress.IPv4Address):
                end = ipaddress.ip_address(end)
            self.end = end
        self.leases = []

    def add_lease(self, nic):
        self._clean_leases()
        self.leases.sort()
        next_ip = self.start
        ips = [n.ip4_address for n in self.leases]
        while next_ip < self.end:
            if next_ip not in ips:
                break
            next_ip += 1
        if next_ip in ips:
            raise DuplicateDhcpAddress(next_ip)
        nic.set_ip4_address(next_ip)
        self.leases.append(nic)
        self.leases.sort()

    def remove_lease(self, addr):
        self._clean_leases()
        for n in self.leases[:]:
            if str(n.ip4_address) == addr:
                self.leases.remove(n)
    
    def _clean_leases(self):
        for n in self.leases[:]:
            if n.ip4_address is None:
                self.leases.remove(n)