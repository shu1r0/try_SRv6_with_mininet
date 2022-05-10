from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import Node
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import Node


class SRv6Node(Node):

    def __init__(self, name, **params):
        super().__init__(name, **params)

    def config(self, **params):
        self.cmd("ifconfig lo up")
        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        self.cmd("sysctl -w net.ipv6.conf.all.forwarding=1")
        self.cmd("sysctl -w net.ipv6.conf.all.seg6_enabled=1")
        self.cmd("sysctl -w net.ipv6.conf.all.seg6_require_hmac=0")

        for i in self.nameToIntf.keys():
            self.cmd("sysctl -w net.ipv6.conf.{}.seg6_enabled=1".format(i))


def main():
    setLogLevel("info")
    net = Mininet()

    r1 = net.addHost("r1", cls=SRv6Node)
    r2 = net.addHost("r2", cls=SRv6Node)
    r3 = net.addHost("r3", cls=SRv6Node)
    r4 = net.addHost("r4", cls=SRv6Node)
    r5 = net.addHost("r5", cls=SRv6Node)
    r6 = net.addHost("r6", cls=SRv6Node)

    h1 = net.addHost("h1", ip=None)
    h2 = net.addHost("h2", ip=None)
    h3 = net.addHost("h3", ip=None)
    h4 = net.addHost("h4", ip=None)

    net.addLink(r1, h1,
                intfName1="r1_h1", params1={"ip": "192.168.1.1/24"},
                intfName2="h1_r1", params2={"ip": "192.168.1.2/24"})
    h1.cmd("ip route add default dev h1_r1 via 192.168.1.1")
    
    net.addLink(r1, h2,
                intfName1="r1_h2", params1={"ip": "192.168.2.1/24"},
                intfName2="h2_r1", params2={"ip": "192.168.2.2/24"})
    h2.cmd("ip route add default dev h2_r1 via 192.168.2.1")
    
    net.addLink(r6, h3,
                intfName1="r6_h3", params1={"ip": "192.168.3.1/24"},
                intfName2="h3_r6", params2={"ip": "192.168.3.2/24"})
    h3.cmd("ip route add default dev h3_r6 via 192.168.3.1")
    
    net.addLink(r6, h4,
                intfName1="r6_h4", params1={"ip": "192.168.4.1/24"},
                intfName2="h4_r6", params2={"ip": "192.168.4.2/24"})
    h4.cmd("ip route add default dev h4_r6 via 192.168.4.1")

    net.addLink(r1, r2, intfName1="r1_r2", intfName2="r2_r1")
    net.addLink(r1, r3, intfName1="r1_r3", intfName2="r3_r1")

    net.addLink(r2, r4, intfName1="r2_r4", intfName2="r4_r2")
    net.addLink(r2, r3, intfName1="r2_r3", intfName2="r3_r2")

    net.addLink(r3, r5, intfName1="r3_r5", intfName2="r5_r3")

    net.addLink(r4, r6, intfName1="r4_r6", intfName2="r6_r4")
    net.addLink(r4, r5, intfName1="r4_r5", intfName2="r5_r4")

    net.addLink(r5, r6, intfName1="r5_r6", intfName2="r6_r5")

    net.start()

    h1.cmd("ip -6 addr add fc00:1::2/64 dev h1_r1")
    h1.cmd("ip -6 route add default dev h1_r1 via fc00:1::1")
    r1.cmd("ip -6 addr add fc00:1::1/64 dev r1_h1")
    
    h2.cmd("ip -6 addr add fc00:2::2/64 dev h2_r1")
    h2.cmd("ip -6 route add default dev h2_r1 via fc00:2::1")
    r1.cmd("ip -6 addr add fc00:2::1/64 dev r1_h2")

    r1.cmd("ip -6 addr add fc00:a::1/64 dev r1_r2")
    r2.cmd("ip -6 addr add fc00:a::2/64 dev r2_r1")

    r1.cmd("ip -6 addr add fc00:b::1/64 dev r1_r3")
    r3.cmd("ip -6 addr add fc00:b::2/64 dev r3_r1")

    r2.cmd("ip -6 addr add fc00:c::1/64 dev r2_r3")
    r3.cmd("ip -6 addr add fc00:c::2/64 dev r3_r2")

    r2.cmd("ip -6 addr add fc00:d::1/64 dev r2_r4")
    r4.cmd("ip -6 addr add fc00:d::2/64 dev r4_r2")

    r3.cmd("ip -6 addr add fc00:e::1/64 dev r3_r5")
    r5.cmd("ip -6 addr add fc00:e::2/64 dev r5_r3")

    r4.cmd("ip -6 addr add fc00:f::1/64 dev r4_r5")
    r5.cmd("ip -6 addr add fc00:f::2/64 dev r5_r4")

    r4.cmd("ip -6 addr add fc00:aa::1/64 dev r4_r6")
    r6.cmd("ip -6 addr add fc00:aa::2/64 dev r6_r4")

    r5.cmd("ip -6 addr add fc00:ab::1/64 dev r5_r6")
    r6.cmd("ip -6 addr add fc00:ab::2/64 dev r6_r5")
    
    h3.cmd("ip -6 addr add fc00:3::2/64 dev h3_r6")
    h3.cmd("ip -6 route add default dev h3_r6 via fc00:3::1")
    r6.cmd("ip -6 addr add fc00:3::1/64 dev r6_h3")
    
    h4.cmd("ip -6 addr add fc00:4::2/64 dev h4_r6")
    h4.cmd("ip -6 route add default dev h4_r6 via fc00:4::1")
    r6.cmd("ip -6 addr add fc00:4::1/64 dev r6_h4")
    
    r1.cmd("ip -6 route add fc00:3::/64 encap seg6 mode encap segs fc00:a::2,fc00:d::2,fc00:aa::2 dev r1_r2")
    r6.cmd("ip -6 route add fc00:1::/64 encap seg6 mode encap segs fc00:ab::1,fc00:e::1,fc00:b::1 dev r6_r5")


    CLI(net)

    net.stop()


if __name__ == "__main__":
    main()
