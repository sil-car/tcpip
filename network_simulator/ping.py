import ipaddress
from .errors import InvalidIPv4Address
from .errors import NextHopNicNotFound
from .errors import NoRouteToHost
from .packets import PingPacket


class Session:
    def __init__(self, source_nic, dest_ip):
        if not source_nic.ip4_address:
            raise InvalidIPv4Address("IPv4 address not defined.")
        self.source_nic = source_nic

        if not isinstance(dest_ip, ipaddress.IPv4Address):
            dest_ip = ipaddress.ip_address(dest_ip)
        self.dest_ip = dest_ip
        self.packet = PingPacket(self.source_nic.ip4_address, self.dest_ip)
    
    def run(self):
        source_nic = self.source_nic
        total_time = None
        while self.dest_ip != source_nic.ip4_address:
            print(f"{self.dest_ip=}; {source_nic.ip4_address=}")
            source_ip = source_nic.ip4_address
            if total_time is None:
                total_time = 0

            time = None
            for ip, link in source_nic.links.items():
                next_hop_nic = self._get_next_hop_nic(source_nic.ip4_address, link)

                # Check for dest_ip.
                if ip == self.dest_ip:
                    time = link.transmit(self.packet)
                    # source_nic = self._get_next_hop_nic(source_nic.ip4_address, link)

                # Check for gateway
                elif ip == source_nic.ip4_gateway:
                    time = link.transmit(self.packet)
                    # source_nic = self._get_next_hop_nic(source_nic.ip4_address, link)

                # Check for public link.
                elif link.public:
                    time = link.transmit(self.packet)
                    # source_nic = self._get_next_hop_nic(source_nic.ip4_address, link)

                else:
                    # FIXME: What if self.source_nic is not directly connected
                    # to the gateway?
                    # NOTE: The line below leads to an infinite loop.
                    # time = link.transmit(self.packet)
                    pass

                if time:  # valid link found
                    source_nic = next_hop_nic
                    break
                
            if time is None:  # no suitable link found
                raise NoRouteToHost(source_ip, self.dest_ip)

            total_time += time
        
        return total_time
    
    def _get_next_hop_nic(self, source_ip, link):
        """Returns the NIC from link.nics at the other end of the link from
        source_ip.
        """
        if link.dest_nic.ip4_address == source_ip:
            return link.source_nic
        elif link.source_nic.ip4_address == source_ip:
            return link.dest_nic
        raise NextHopNicNotFound


def ping(source_nic, dest_ip):
    """Execute ping command from given source NIC to given IP address and return
    total response time.
    """
    ping_session = Session(source_nic, dest_ip)
    return ping_session.run()
