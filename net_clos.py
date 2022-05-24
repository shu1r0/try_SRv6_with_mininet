from mininet.cli import CLI
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import Node

daemons = """
zebra=yes
bgpd=yes

vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
bgpd_options="   --daemon -A 127.0.0.1"
"""

vtysh = """
hostname {name}
service integrated-vtysh-config
"""

super_spine_conf = """\
enable
configure terminal
router bgp 65000
  bgp router-id {router_id}
  no bgp default ipv4-unicast
  no bgp ebgp-requires-policy
  neighbor CLOS peer-group
  neighbor CLOS remote-as external
  neighbor CLOS capability extended-nexthop
  neighbor CLOS bfd
  neighbor {ss_name}_s1 interface peer-group CLOS
  neighbor {ss_name}_s2 interface peer-group CLOS
  neighbor {ss_name}_s3 interface peer-group CLOS
  neighbor {ss_name}_s4 interface peer-group CLOS
  neighbor {ss_name}_s1 capability extended-nexthop
  neighbor {ss_name}_s2 capability extended-nexthop
  neighbor {ss_name}_s3 capability extended-nexthop
  neighbor {ss_name}_s4 capability extended-nexthop
  address-family ipv6 unicast
    redistribute connected
    neighbor CLOS activate
  exit-address-family
"""

spine_conf = """\
enable
configure terminal
router bgp {as_number}
  bgp router-id {router_id}
  no bgp default ipv4-unicast
  no bgp ebgp-requires-policy
  bgp bestpath as-path multipath-relax
  neighbor CLOS peer-group
  neighbor CLOS remote-as external
  neighbor CLOS bfd
  neighbor CLOS capability extended-nexthop
  neighbor {s_name}_ss1 interface peer-group CLOS
  neighbor {s_name}_ss2 interface peer-group CLOS
  neighbor {s_name}_ss3 interface peer-group CLOS
  neighbor {s_name}_ss4 interface peer-group CLOS
  neighbor {s_name}_{l_name1} interface peer-group CLOS
  neighbor {s_name}_{l_name2} interface peer-group CLOS
  neighbor {s_name}_ss1 capability extended-nexthop
  neighbor {s_name}_ss2 capability extended-nexthop
  neighbor {s_name}_ss3 capability extended-nexthop
  neighbor {s_name}_ss4 capability extended-nexthop
  neighbor {s_name}_{l_name1} capability extended-nexthop
  neighbor {s_name}_{l_name2} capability extended-nexthop
  address-family ipv6 unicast
    redistribute connected
    neighbor CLOS activate
  exit-address-family
"""

leaf_conf = """\
enable
configure terminal
router bgp {as_number}
  bgp router-id {router_id}
  no bgp default ipv4-unicast
  no bgp ebgp-requires-policy
  bgp bestpath as-path multipath-relax
  neighbor CLOS peer-group
  neighbor CLOS remote-as external
  neighbor CLOS bfd
  neighbor CLOS capability extended-nexthop
  neighbor {l_name}_{s_name1} interface peer-group CLOS
  neighbor {l_name}_{s_name2} interface peer-group CLOS
  neighbor {l_name}_{s_name1} capability extended-nexthop
  neighbor {l_name}_{s_name2} capability extended-nexthop
  address-family ipv6 unicast
    redistribute connected
    neighbor CLOS activate
  exit-address-family
"""

no_ipv6_nd = """\
enable
configure terminal
interface {}
no ipv6 nd suppress-ra
"""

class SRv6Node(Node):

    def __init__(self, name, **params):
        super().__init__(name, **params)

    def config(self, **params):
        # self.cmd("hostname " + self.name)
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
        self.set_conf("/etc/frr/frr.conf", "")
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
    

class Leaf(FRR):
    pass

class Spine(FRR):
    pass

class SuperSpine(FRR):
    pass


def main():
    setLogLevel("info")
    net = Mininet()

    l1 = net.addHost("l1", cls=Leaf)
    l2 = net.addHost("l2", cls=Leaf)
    l3 = net.addHost("l3", cls=Leaf)
    l4 = net.addHost("l4", cls=Leaf)
    
    s1 = net.addHost("s1", cls=Spine)
    s2 = net.addHost("s2", cls=Spine)
    s3 = net.addHost("s3", cls=Spine)
    s4 = net.addHost("s4", cls=Spine)
    
    ss1 = net.addHost("ss1", cls=SuperSpine)
    ss2 = net.addHost("ss2", cls=SuperSpine)
    ss3 = net.addHost("ss3", cls=SuperSpine)
    ss4 = net.addHost("ss4", cls=SuperSpine)

    # host
    h1 = net.addHost("h1", ip=None)
    h2 = net.addHost("h2", ip=None)
    h3 = net.addHost("h3", ip=None)
    h4 = net.addHost("h4", ip=None)
    h5 = net.addHost("h5", ip=None)
    h6 = net.addHost("h6", ip=None)
    h7 = net.addHost("h7", ip=None)
    h8 = net.addHost("h8", ip=None)
    
    def set_link(n1, n2, block):
        intf1 = str(n1)+"_"+str(n2)
        intf2 = str(n2)+"_"+str(n1)
        net.addLink(n1, n2, intfName1=intf1, intfName2=intf2)
        
        ipv6_1 = "fc00::{}:1:0:0/96".format(block)
        ipv6_2 = "fc00::{}:2:0:0/96".format(block)
        n1.cmd("ip -6 addr add {} dev {}".format(ipv6_1, intf1))
        n2.cmd("ip -6 addr add {} dev {}".format(ipv6_2, intf2))
    
    def set_link_super_spine(block):
        block = int(block)
        sspines = [n for n in net.nameToNode.values() if isinstance(n, SuperSpine)]
        spines = [n for n in net.nameToNode.values() if isinstance(n, Spine)]
        for ss in sspines:
            for s in spines:
                block = block + 1
                set_link(ss, s, block)
    
    def set_link_pod(s1, s2, l1, l2, block):
        block = int(block)
        for s in [s1, s2]:
            for l in [l1, l2]:
                block = block + 1
                set_link(s, l, block)
    
    def set_link_hosts(r, h1, h2, block):
        
        def set_link_host(r, n, block):
            ipv6_1 = "fc00::{}:1:0:0/96".format(block)
            ipv6_2 = "fc00::{}:2:0:0/96".format(block)
            ipv4_1 = "192.168.{}.1/24".format(block)
            ipv4_2 = "192.168.{}.2/24".format(block)
            intf1 = str(r)+"_"+str(n)
            intf2 = str(n)+"_"+str(r)
            net.addLink(r, n, 
                        intfName1=intf1, params1={"ip": ipv4_1},
                        intfName2=intf2, params2={"ip": ipv4_2})
            r.cmd("ip -6 addr add {} dev {}".format(ipv6_1, intf1))
            n.cmd("ip -6 addr add {} dev {}".format(ipv6_2, intf2))
            
            n.cmd("ip route add default dev {} via {}".format(intf2, ipv4_1))
            n.cmd("ip -6 route add default dev {} via {}".format(intf2, ipv6_1))
            
        set_link_host(r, h1, block)
        set_link_host(r, h2, int(block)+1)
    
    
    set_link_super_spine("300")
    
    set_link_pod(s1, s2, l1, l2, "200")
    set_link_pod(s3, s4, l3, l4, "210")
    
    set_link_hosts(l1, h1, h2, "110")
    set_link_hosts(l2, h3, h4, "120")
    set_link_hosts(l3, h5, h6, "130")
    set_link_hosts(l4, h7, h8, "140")
    
    net.start()
    
    
    
    # frr setup
    def set_frr_superspine(ss, router_id):
        ss.vtysh_cmd(super_spine_conf.format(
            router_id=router_id,
            ss_name=str(ss)
        ))
        
    def set_frr_spine(s, router_id, as_number, l1, l2):
        s.vtysh_cmd(spine_conf.format(
            as_number=as_number,
            router_id=router_id,
            s_name=str(s),
            l_name1=str(l1),
            l_name2=str(l2)
        ))
        
    def set_frr_leaf(l, router_id, as_number, s1, s2):
        l.vtysh_cmd(leaf_conf.format(
            as_number=as_number,
            router_id=router_id,
            l_name=str(l),
            s_name1=str(s1),
            s_name2=str(s2)
        ))
    
    set_frr_superspine(ss1, "1.1.1.1")
    set_frr_superspine(ss2, "1.1.1.2")
    set_frr_superspine(ss3, "1.1.1.3")
    set_frr_superspine(ss4, "1.1.1.4")
    
    set_frr_spine(s1, "2.2.2.1", 65103, l1, l2)
    set_frr_spine(s2, "2.2.2.2", 65104, l1, l2)
    set_frr_spine(s3, "2.2.2.3", 65203, l3, l4)
    set_frr_spine(s4, "2.2.2.4", 65204, l3, l4)
    
    set_frr_leaf(l1, "3.3.3.1", 65101, s1, s2)
    set_frr_leaf(l2, "3.3.3.2", 65102, s1, s2)
    set_frr_leaf(l3, "3.3.3.3", 65201, s3, s4)
    set_frr_leaf(l4, "3.3.3.4", 65202, s3, s4)
    
    for n in net.nameToNode.values():
        if isinstance(n, FRR):
            for i in n.nameToIntf.keys():
                n.vtysh_cmd(no_ipv6_nd.format(i))
    
    
    CLI(net)
    net.stop()


if __name__ == "__main__":
    main()
