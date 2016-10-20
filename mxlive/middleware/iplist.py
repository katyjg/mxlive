from ipaddr import IPNetwork, IPAddress

    
class IPAddressList(list):

    def __init__(self, *ips):
        self.extend([IPNetwork(ip) for ip in ips])
             
    def __contains__(self, address):
        ip = IPAddress(address)
        return any(ip in net for net in self)
            

