from mininet.cli import CLI
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import Node

daemons = """
zebra=yes
ospf6d=yes

vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
ospf6d_options=" --daemon -A ::1"
"""

vtysh = """
hostname {name}
service integrated-vtysh-config
"""

r1_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 1.1.1.1
exit

interface r1_h1
ipv6 ospf6 area 0.0.0.0
interface r1_h3
ipv6 ospf6 area 0.0.0.0
interface r1_r2
ipv6 ospf6 area 0.0.0.0
interface r1_r3
ipv6 ospf6 area 0.0.0.0
"""

r2_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 2.2.2.2
exit

interface r2_r1
ipv6 ospf6 area 0.0.0.0
interface r2_r3
ipv6 ospf6 area 0.0.0.0
interface r2_r4
ipv6 ospf6 area 0.0.0.0
interface r2_s1
ipv6 ospf6 area 0.0.0.0
"""

r3_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 3.3.3.3
exit

interface r3_r1
ipv6 ospf6 area 0.0.0.0
interface r3_r2
ipv6 ospf6 area 0.0.0.0
interface r3_r5
ipv6 ospf6 area 0.0.0.0
"""

r4_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 4.4.4.4
exit

interface r4_r2
ipv6 ospf6 area 0.0.0.0
interface r4_r5
ipv6 ospf6 area 0.0.0.0
interface r4_r6
ipv6 ospf6 area 0.0.0.0
interface r4_s2
ipv6 ospf6 area 0.0.0.0
"""


r5_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 5.5.5.5
exit

interface r5_r3
ipv6 ospf6 area 0.0.0.0
interface r5_r4
ipv6 ospf6 area 0.0.0.0
interface r5_r6
ipv6 ospf6 area 0.0.0.0
"""


r6_conf = """\
enable
configure terminal
router ospf6
ospf6 router-id 6.6.6.6
exit

interface r6_r4
ipv6 ospf6 area 0.0.0.0
interface r6_r5
ipv6 ospf6 area 0.0.0.0
interface r6_h3
ipv6 ospf6 area 0.0.0.0
interface r6_h4
ipv6 ospf6 area 0.0.0.0
"""


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


class FRR(SRv6Node):
    """FRR Node"""

    PrivateDirs = ["/etc/frr", "/var/run/frr"]

    def __init__(self, name, inNamespace=True, **params):
        params.setdefault("privateDirs", [])
        params["privateDirs"].extend(self.PrivateDirs)
        super().__init__(name, inNamespace=inNamespace, **params)
        
    def config(self, **params):
        super().config(**params)
        self.start_frr_service()

    def start_frr_service(self):
        """start FRR"""
        self.set_conf("/etc/frr/daemons", daemons)
        self.set_conf("/etc/frr/vtysh.conf", vtysh.format(name=self.name))
        print(self.cmd("/usr/lib/frr/frrinit.sh start"))

    def set_conf(self, file, conf):
        """set frr config"""
        self.cmd("""\
cat << 'EOF' | tee {}
{}
EOF""".format(file, conf))

    def vtysh_cmd(self, cmd=""):
        """exec vtysh commands"""
        cmds = cmd.split("\n")
        vtysh_cmd = "vtysh"
        for c in cmds:
            vtysh_cmd += " -c \"{}\"".format(c)
        return self.cmd(vtysh_cmd)


def main():
    setLogLevel("info")
    net = Mininet()

    # add frr node
    r1 = net.addHost("r1", cls=FRR)
    r2 = net.addHost("r2", cls=FRR)
    r3 = net.addHost("r3", cls=FRR)
    r4 = net.addHost("r4", cls=FRR)
    r5 = net.addHost("r5", cls=FRR)
    r6 = net.addHost("r6", cls=FRR)
    
    # services
    s1 = net.addHost("s1", cls=SRv6Node)
    s2 = net.addHost("s2", cls=SRv6Node)

    # host
    h1 = net.addHost("h1", ip=None)
    h2 = net.addHost("h2", ip=None)
    h3 = net.addHost("h3", ip=None)
    h4 = net.addHost("h4", ip=None)

    # config link
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
    net.addLink(r2, s1, intfName1="r2_s1", intfName2="s1_r2")

    net.addLink(r3, r5, intfName1="r3_r5", intfName2="r5_r3")

    net.addLink(r4, r6, intfName1="r4_r6", intfName2="r6_r4")
    net.addLink(r4, r5, intfName1="r4_r5", intfName2="r5_r4")
    net.addLink(r4, s2, intfName1="r4_s2", intfName2="s2_r4")

    net.addLink(r5, r6, intfName1="r5_r6", intfName2="r6_r5")

    # set address
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
    
    s1.cmd("ip -6 addr add fc00:fff1::2/64 dev s1_r2")
    s1.cmd("ip -6 route add default dev s1_r2 via fc00:fff1::1")
    r2.cmd("ip -6 addr add fc00:fff1::1/64 dev r2_s1")
    
    s2.cmd("ip -6 addr add fc00:fff2::2/64 dev s2_r4")
    s2.cmd("ip -6 route add default dev s2_r4 via fc00:fff2::1")
    r4.cmd("ip -6 addr add fc00:fff2::1/64 dev r4_s2")
    
    # add route
    r1.cmd("ip -6 route add fc00:3::2/128 encap seg6 mode encap segs fc00:fff1::2,fc00:fff2::2,fc00:3::1:2 dev r1_r2")
    r6.cmd("ip -6 route add fc00:3::1:2/128 encap seg6local action End.DX6 nh6 fc00:3::2 dev r6_h3")
    
    net.start()
    
    r1.vtysh_cmd(r1_conf)
    r2.vtysh_cmd(r2_conf)
    r3.vtysh_cmd(r3_conf)
    r4.vtysh_cmd(r4_conf)
    r5.vtysh_cmd(r5_conf)
    r6.vtysh_cmd(r6_conf)

    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
