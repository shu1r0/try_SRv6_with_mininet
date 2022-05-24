from mininet.cli import CLI
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import Node

daemons = """
zebra=yes
bgpd=no
ospfd=no
ospf6d=no
ripd=no
ripngd=no
isisd=no
pimd=no
ldpd=no
nhrpd=no
eigrpd=no
babeld=no
sharpd=no
staticd=no
pbrd=no
bfdd=no
fabricd=no

vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
bgpd_options="   --daemon -A 127.0.0.1"
ospfd_options="  --daemon -A 127.0.0.1"
ospf6d_options=" --daemon -A ::1"
ripd_options="   --daemon -A 127.0.0.1"
ripngd_options=" --daemon -A ::1"
isisd_options="  --daemon -A 127.0.0.1"
pimd_options="  --daemon -A 127.0.0.1"
ldpd_options="  --daemon -A 127.0.0.1"
nhrpd_options="  --daemon -A 127.0.0.1"
eigrpd_options="  --daemon -A 127.0.0.1"
babeld_options="  --daemon -A 127.0.0.1"
sharpd_options="  --daemon -A 127.0.0.1"
staticd_options="  --daemon -A 127.0.0.1"
pbrd_options="  --daemon -A 127.0.0.1"
bfdd_options="  --daemon -A 127.0.0.1"
fabricd_options="  --daemon -A 127.0.0.1"
"""

vtysh = """
hostname {name}
service integrated-vtysh-config
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
    
    def add_seg6route(self, dst, oif, encap):
        self.cmd("python3 -c \"from pyroute2 import IPRoute;ipr = IPRoute();ipr.route('add', dst='{dst}', oif=ipr.link_lookup(ifname='{oif}')[0], encap={encap})\"".format(dst=dst, oif=oif, encap=encap))




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
        # self.set_conf("/etc/frr/frr.conf", frr)
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
    
    r4.cmd("ip -6 route add fc00:3::/64 dev r4_r6 via fc00:aa::2")
    r4.cmd("ip -6 route add fc00:4::/64 dev r4_r6 via fc00:aa::2")
    
    r3.cmd("ip -6 route add fc00:1::/64 dev r3_r1 via fc00:b::1")
    r3.cmd("ip -6 route add fc00:2::/64 dev r3_r1 via fc00:b::1")
    
    # r1.cmd("ip route add 192.168.3.2/32 encap seg6 mode encap segs fc00:a::2,fc00:d::2,fc00:3::2 oif r1_r2 dev r1_r2")
    # r1.cmd("ip route add 192.168.4.2/32 encap seg6 mode encap segs fc00:a::2,fc00:d::2,fc00:4::2 oif r1_r2 dev r1_r2")
    r6.cmd("ip route add 192.168.1.2/32 encap seg6 mode encap segs fc00:ab::1,fc00:e::1,fc00:1::2 oif r6_r5 dev r6_r5")
    r6.cmd("ip route add 192.168.2.2/32 encap seg6 mode encap segs fc00:ab::1,fc00:e::1,fc00:2::2 oif r6_r5 dev r6_r5")
    
    # r1.cmd("ip -6 route add fc00:1::2/128 encap seg6local action End.DX4 nh4 192.168.1.2 oif r1_h1 dev r1_h1")
    # r1.cmd("ip -6 route add fc00:2::2/128 encap seg6local action End.DX4 nh4 192.168.2.2 oif r1_h2 dev r1_h2")
    # r6.cmd("ip -6 route add fc00:3::2/128 encap seg6local action End.DX4 nh4 192.168.3.2 oif r6_h3 dev r6_h3")
    # r6.cmd("ip -6 route add fc00:4::2/128 encap seg6local action End.DX4 nh4 192.168.4.2 oif r6_h4 dev r6_h4")
    
    r1.add_seg6route("192.168.3.2/32", "r1_r2", "{'type': 'seg6', 'mode': 'encap', 'segs': ['fc00:a::2','fc00:d::2','fc00:3::2'][::-1]}")
    r1.add_seg6route("192.168.4.2/32", "r1_r2", "{'type': 'seg6', 'mode': 'encap', 'segs': ['fc00:a::2','fc00:d::2','fc00:4::2'][::-1]}")
    # r6.add_seg6route("192.168.3.2/32", "r6_r5", "{'type': 'seg6', 'mode': 'encap', 'segs': ['fc00:a::2','fc00:d::2','fc00:3::2']}")
    
    r1.add_seg6route("fc00:1::2/128", "r1_h1", "{'type': 'seg6local', 'action': 'End.DX4', 'nh4': '192.168.1.2'}")
    r1.add_seg6route("fc00:2::2/128", "r1_h1", "{'type': 'seg6local', 'action': 'End.DX4', 'nh4': '192.168.2.2'}")
    r6.add_seg6route("fc00:3::2/128", "r6_h3", "{'type': 'seg6local', 'action': 'End.DX4', 'nh4': '192.168.3.2'}")
    r6.add_seg6route("fc00:4::2/128", "r6_h4", "{'type': 'seg6local', 'action': 'End.DX4', 'nh4': '192.168.4.2'}")

    net.start()
    CLI(net)
    net.stop()


def main2():
    setLogLevel("info")
    net = Mininet()

    r1 = net.addHost("r1", cls=SRv6Node)
    r2 = net.addHost("r2", cls=SRv6Node)
    h1 = net.addHost("h1", ip=None)
    h2 = net.addHost("h2", ip=None)

    net.addLink(r1, h1,
                intfName1="r1_h1", params1={"ip": "192.168.1.1/24"},
                intfName2="h1_r1", params2={"ip": "192.168.1.2/24"})
    h1.cmd("ip route add default dev h1_r1 via 192.168.1.1")
    
    net.addLink(r2, h2,
                intfName1="r2_h2", params1={"ip": "192.168.2.1/24"},
                intfName2="h2_r2", params2={"ip": "192.168.2.2/24"})
    h2.cmd("ip route add default dev h2_r2 via 192.168.2.1")

    net.addLink(r1, r2, intfName1="r1_r2", intfName2="r2_r1")

    h1.cmd("ip -6 addr add fc00:1::2/64 dev h1_r1")
    h1.cmd("ip -6 route add default dev h1_r1 via fc00:1::1")
    r1.cmd("ip -6 addr add fc00:1::1/64 dev r1_h1")
    
    h2.cmd("ip -6 addr add fc00:2::2/64 dev h2_r2")
    h2.cmd("ip -6 route add default dev h2_r2 via fc00:2::1")
    r2.cmd("ip -6 addr add fc00:2::1/64 dev r2_h2")

    r1.cmd("ip -6 addr add fc00:a::1/64 dev r1_r2")
    r2.cmd("ip -6 addr add fc00:a::2/64 dev r2_r1")
    
    r1.cmd("ip -6 route add fc00:2::/64 via fc00:a::2 dev r1_r2")
    r1.cmd("ip route add 192.168.2.2/32 encap seg6 mode encap segs fc00:2::2 dev r1_r2")
    
    # r1.cmd("ip -6 route add fc00:1::2/128 encap seg6local action End.DX4 nh4 192.168.1.2 oif r1_h1 dev r1_h1")
    # r1.cmd("ip -6 route add fc00:2::2/128 encap seg6local action End.DX4 nh4 192.168.2.2 oif r1_h2 dev r1_h2")
    r2.cmd("ip -6 route add fc00:2::2/128 encap seg6local action End.DX4 nh4 192.168.2.2 dev r2_h2")

    net.start()
    CLI(net)
    net.stop()

if __name__ == "__main__":
    main2()
