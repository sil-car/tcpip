import ipaddress
from .constants import FIBER_LATENCY
from .constants import FIBER_THROUGHPUT
from .constants import COPPER_LATENCY
from .constants import COPPER_THROUGHPUT
from .constants import WIFI_LATENCY
from .constants import WIFI_THROUGHPUT
from .errors import InvalidIPv4Address
from .errors import InvalidNetworkConfig
from .errors import NoNetworkConnection


class Link:
    """Base class for network links between NICs."""
    def __init__(self, source_nic, dest_nic, bandwidth, latency, public):
        self.public = public
        self.bandwidth = bandwidth  # Bandwidth in bits per second
        self.latency = latency  # milliseconds
        self.source_nic = source_nic
        self.dest_nic = dest_nic

    def transmit(self, packet):
        """Returns time in milliseconds required to send packet."""
        return self.latency + (packet.size * 8 * 1000 / self.bandwidth)


class EthLink(Link):
    """Used for ethernet links."""
    def __init__(self, source_nic, dest_nic, bandwidth=None, latency=None, public=None):
        if bandwidth is None:
            bandwidth = COPPER_THROUGHPUT
        if latency is None:
            latency = COPPER_LATENCY
        if public is None:
            public = False
        super().__init__(source_nic, dest_nic, bandwidth=bandwidth, latency=latency, public=public)


class OptLink(Link):
    """Used for optical links."""
    def __init__(self, source_nic, dest_nic, bandwidth=None, latency=None, public=None):
        if bandwidth is None:
            bandwidth = FIBER_THROUGHPUT
        if latency is None:
            latency = FIBER_LATENCY
        if public is None:
            public = False
        super().__init__(source_nic, dest_nic, bandwidth=bandwidth, latency=latency, public=public)


class PublicLink(OptLink):
    """Used for unknown links to the public Internet."""
    def __init__(self, source_nic, dest_nic):
        super().__init__(source_nic, dest_nic, public=True)


class WifiLink(Link):
    """Used for WiFi links."""
    def __init__(self, source_nic, dest_nic, bandwidth=None, latency=None, public=None):
        if bandwidth is None:
            bandwidth = WIFI_THROUGHPUT
        if latency is None:
            latency = WIFI_LATENCY
        if public is None:
            public = False
        super().__init__(source_nic, dest_nic, bandwidth=bandwidth, latency=latency, public=public)


class Nic:
    def __init__(
        self,
        address=None,
        dhcp=None,
        gateway=None,
        idx=None,
        network=None,
        public=None
    ):
        self.throughput = None
        self.links = dict()
        self.name = None
        self.dhcp = dhcp
        self.idx = idx

        self.public = False
        if public:
            self.public = public
        self.ip4_network = None
        if network:
            self.set_ip4_network(network)
        self.ip4_gateway = None
        if gateway:
            self.set_ip4_gateway(gateway)
        self.ip4_address = None
        if address:
            self.set_ip4_address(address)  # must be set after self.ip4_network
    
    def __lt__(self, other):
        return self.ip4_address < other.ip4_address

    def __str__(self):
        return self.name

    def add_link(self, dest_nic, address=None, dhcp=None, gateway=None, network=None):
        if dest_nic.dhcp:
            self.set_ip4_network(dest_nic.ip4_network)
            self.set_ip4_gateway(dest_nic.ip4_gateway)
            dest_nic.dhcp.add_lease(self)
        elif address and network:
            self.set_ip4_network(network)
            self.set_ip4_address(address)
            if gateway:
                self.set_ip4_gateway(gateway)

        # If dest_nic is Public, assume link is PublicLink type regardless of source_nic type.
        if isinstance(dest_nic, Public):
            link_class = PublicLink
        # Otherwise set link type according to source_nic type.
        elif isinstance(self, Eth):
            link_class = EthLink
        elif isinstance(self, Wifi):
            link_class = WifiLink
        elif isinstance(self, Opt):
            link_class = OptLink

        link = link_class(self, dest_nic)
        dest_nic.links[self.ip4_address] = link
        self.links[dest_nic.ip4_address] = link

    def remove_link(self, dest_nic):
        del dest_nic.links[self.ip4_address]
        del self.links[dest_nic.ip4_address]
        self._reset_network()

    def set_ip4_network(self, ip_and_subnet: str) -> None:
        """Input must be in the format '0.0.0.0/0'."""
        self.ip4_network = ipaddress.ip_network(ip_and_subnet, strict=False)

    def set_ip4_address(self, addr: str, gateway: bool = False) -> None:
        if not self.public:
            if not self.ip4_network:
                raise InvalidNetworkConfig("IPv4 network not defined.")
            if not self._is_local(addr):
                raise InvalidIPv4Address("IPv4 address not in defined network.")
        if gateway:
            self.ip4_gateway = ipaddress.ip_address(addr)
        else:
            self.ip4_address = ipaddress.ip_address(addr)

    def set_ip4_gateway(self, addr) -> None:
        self.set_ip4_address(addr, gateway=True)

    def is_connected(self) -> bool:
        return len(self.links) > 0

    def _is_gateway(self) -> bool:
        """Returns whether object's given IPv4 address is the gateway address."""
        if not self.ip4_address:
            raise InvalidIPv4Address("IPv4 address not defined.")
        if not self.ip4_gateway:
            raise InvalidIPv4Address("IPv4 Gateway not defined.")
        return self.ip4_address == self.ip4_gateway

    def _is_local(self, dest: str|ipaddress.IPv4Address) -> bool:
        """Returns whether given IP address is found in the local IP network."""
        if not self.ip4_network:
            raise InvalidNetworkConfig("IPv4 network not defined.")
        if not isinstance(dest, ipaddress.IPv4Address):
            dest = ipaddress.ip_address(dest)
        return dest in [h for h in self.ip4_network.hosts()]

    def _get_response_time(self) -> float:
        """Returns response time in ms if connected."""
        if self.is_connected():
            return self.latency
        raise NoNetworkConnection

    def _get_nic_from_ipaddr(self, addr: str|ipaddress.IPv4Address):
        if self._is_local(addr):
            # Check direct connections to current NIC.
            for nic in self.links:
                if nic.ip4_address == addr:
                    return nic
                # Check gateway NIC connections.
                if nic.ip4_address == nic.ip4_gateway:
                    for n in nic.links:
                        if n.ip4_address == addr:
                            return n
        else:
            return Public(address=addr)

    def _get_nic_from_link(self, ipaddr, link):
        for nic in link.nics:
            if nic.ip4_address == ipaddr:
                return nic
                break
    
    def _reset_network(self):
        self.ip4_address = None
        self.ip4_gateway = None
        self.ip4_network = None


class Public(Nic):
    def __init__(self, address=None):
        super().__init__(address=address, public=True)
        self.latency = FIBER_LATENCY
        self.throughput = FIBER_THROUGHPUT


class Eth(Nic):
    def __init__(self, idx=0, **kwargs):
        super().__init__(idx=idx, **kwargs)
        self.latency = COPPER_LATENCY
        self.throughput = COPPER_THROUGHPUT
        self.idx = idx
        self.name = f"eth{self.idx}"


class Opt(Nic):
    def __init__(self, address=None, gateway=None, idx=0, network=None):
        super().__init__(address=address, gateway=gateway, idx=idx, network=network)
        self.latency = FIBER_LATENCY
        self.throughput = FIBER_THROUGHPUT
        self.idx = idx
        self.name = f"opt{self.idx}"

class Wifi(Nic):
    def __init__(self, address=None, gateway=None, idx=0, network=None):
        super().__init__(address=address, gateway=gateway, idx=idx, network=network)
        self.latency = WIFI_LATENCY
        self.throughput = WIFI_THROUGHPUT
        self.idx = idx
        self.name = f"wlan{self.idx}"
