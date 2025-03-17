class Packet:
    def __init__(self, size, src, dest):
        self.size = size
        self.src = src
        self.dest = dest    


class PingPacket(Packet):
    def __init__(self, src, dest):
        super().__init__(size=32, src=src, dest=dest)