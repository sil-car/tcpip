# Base exception
class NetworkError(Exception):
    DEFAULT_MESSAGE = "Network error."
    def __init__(self, message=None):
        if message:
            self.message = message
        else:
            self.message = self.DEFAULT_MESSAGE

    def __str__(self):
        return self.message


# Network configuration errors
class InvalidNetworkConfig(NetworkError):
    DEFAULT_MESSAGE = "Bad network configuration."

class NoNetworkConfig(InvalidNetworkConfig):
    DEFAULT_MESSAGE = "Network not configured."

class InvalidIPAddress(InvalidNetworkConfig):
    DEFAULT_MESSAGE = "Bad IP Address."

class NoIPAddress(InvalidIPAddress):
    DEFAULT_MESSAGE = "IP address not defined."

class InvalidIPv4Address(InvalidIPAddress):
    DEFAULT_MESSAGE = "Bad IPv4 Address."

class NoIPv4Address(InvalidIPv4Address):
    DEFAULT_MESSAGE = "IPv4 address not defined."

class DuplicateDhcpAddress(InvalidIPv4Address):
    def __init__(self, message=None):
        if message:
            self.message = f"DHCP IPv4 Address not available: {message}"
        else:
            self.message = "DHCP IPv4 Address not available."


# Network connection errors
class NoNetworkConnection(NetworkError):
    DEFAULT_MESSAGE = "Network not connected."

class NextHopNicNotFound(NetworkError):
    DEFAULT_MESSAGE = "Next hop NIC not found."

class NoRouteToHost(NetworkError):
    def __init__(self, src=None, dest=None):
        if src and dest:
            self.message = f"No route found from {src} to {dest}."
        else:
            self.message = "No route found to host."