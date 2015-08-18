
    puts(green("installing MidoNet cli on %s" % env.host_string))

    args = {}

    Puppet.apply('midonet::midonet_cli', args, metadata)

    run("""

cat >/root/.midonetrc <<EOF
[cli]
api_url = http://%s:8080/midonet-api
username = admin
password = admin
project_id = admin
tenant = admin
EOF

""" % metadata.servers[metadata.roles['midonet_api'][0]]['ip'])

    cuisine.package_ensure("expect")

    puts(green("configuring midonet virtual router (using cli on %s)" % env.host_string))

    kdx = 0
    for server in metadata.roles['midonet_gateways']:
        kdx = kdx + 1

        if server == env.host_string:
            idx = kdx * 4

            transfer_network = CIDR(metadata.config["varnish_edge_network"])[idx]

            transfer_overlay_ip = CIDR(metadata.config["varnish_edge_network"])[idx + 1]

            transfer_underlay_ip = CIDR(metadata.config["varnish_edge_network"])[idx + 2]

            overlay_bgp_session = 65000

            underlay_bgp_session = overlay_bgp_session + idx + 2

    #
    # this is the virtual side of the BGP session in the /30 transfer network
    #
    run("""

ROUTER_IP="%s"
GW_IP="%s"
NETWORK="%s"
BGP="%s"
PEER="%s"

midonet-cli -e 'router list' | grep 'name router_edge' || midonet-cli -e 'router add name router_edge'

ROUTER_ID="$(midonet-cli -e "router list name router_edge" | awk '{print $2;}')"

#
# create the northbound edge router port for the veth pair going to the /30
#
midonet-cli -e "router ${ROUTER_ID} port list" | grep "address ${ROUTER_IP} net ${NETWORK}/30" || \
    midonet-cli -e "router ${ROUTER_ID} add port address ${ROUTER_IP} net ${NETWORK}/30"

/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }

expect "midonet> " { send "router list name router_edge\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/30\r" }
expect "midonet> " { send "router router0 add route src 0.0.0.0/0 dst ${GW_IP}/32 type normal weight 10 port router0:port0\r" }

# NO BGP expect "midonet> " { send "router router0 port port0 add bgp local-AS ${BGP} peer-AS ${PEER} peer ${GW_IP}\r" }

expect "midonet> " { send "quit\r" }
EOF

""" % (
        transfer_overlay_ip,
        transfer_underlay_ip,
        transfer_network,
        overlay_bgp_session,
        underlay_bgp_session
    ))

#
# use this for a less fine grained routing
#
# expect "midonet> " { send "router router0 port port0 bgp bgp0 add route net 10.0.0.0/8\r" }

    for server in sorted(metadata.servers):
        if "applications" in metadata.servers[server]:
            for application in sorted(metadata.servers[server]['applications']):
                for container in sorted(metadata.servers[server]['applications'][application]):
                    container_network = metadata.servers[server]['applications'][application][container]['network']
                    run("""
ROUTER_IP="%s"
NETWORK="%s"
ROUTE_NETWORK="%s"

/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }

expect "midonet> " { send "router list name router_edge\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/30\r" }
expect "midonet> " { send "router router0 port port0 list bgp\r" }

# NO BGP expect "midonet> " { send "router router0 port port0 bgp bgp0 add route net ${ROUTE_NETWORK}/30\r" }

expect "midonet> " { send "quit\r" }
EOF

""" % (
        transfer_overlay_ip,
        transfer_network,
        container_network
    ))

    cuisine.package_ensure("quagga")

    #
    # this is the physical side
    #
    run("""

ROUTER_IP="%s"
GW_IP="%s"
NETWORK="%s"

BGP="%s"
PEER="%s"

OVERLAY_MTU="%s"

XHOSTNAME="$(hostname)"

ln -sfv /usr/lib/quagga/bgpd /usr/sbin/bgpd

ip link show | grep -- "underlay" || ip link add "underlay" type veth peer name "overlay"

ip link set "underlay" up
ip link set "overlay" up

ip addr add "${GW_IP}/255.255.255.252" dev underlay

ip link set dev underlay mtu ${OVERLAY_MTU}
ip link set dev overlay mtu ${OVERLAY_MTU}

/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }

expect "midonet> " { send "router list name router_edge\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/30\r" }

expect "midonet> " { send "host list name ${XHOSTNAME}\r" }
expect "midonet> " { send "host host0 add binding port router router0 port port0 interface overlay\r" }

expect "midonet> " { send "quit\r" }
EOF

""" % (
        transfer_overlay_ip,
        transfer_underlay_ip,
        transfer_network,
        overlay_bgp_session,
        underlay_bgp_session,
        metadata.config["overlay_mtu"]
    ))

    run("""

service quagga stop || echo

# NO BGP, otherwise change this to yes
cat >/etc/quagga/daemons <<EOF
zebra=no
bgpd=no
ospfd=no
ospf6d=no
ripd=no
ripngd=no
isisd=no
babeld=no
EOF

rm /etc/quagga/zebra.conf

rm /etc/quagga/bgpd.conf

exit 0

cat >/etc/quagga/zebra.conf <<EOF
hostname $(hostname)
password zebra
enable password zebra
EOF

""")

    run("""

ROUTER_IP="%s"
GW_IP="%s"
NETWORK="%s"

EDGE_NETWORK="%s"

BGP="%s"
PEER="%s"

cat >/etc/quagga/bgpd.conf <<EOF
hostname $(hostname)
password zebra
enable password zebra

log file /var/log/quagga/bgpd.log
log stdout

debug bgp events
debug bgp filters
debug bgp fsm
debug bgp keepalives
debug bgp updates

router bgp ${PEER}
 bgp router-id ${GW_IP}
 bgp cluster-id ${GW_IP}

 neighbor ${ROUTER_IP} remote-as ${BGP}
 neighbor ${ROUTER_IP} next-hop-self
 neighbor ${ROUTER_IP} update-source ${GW_IP}

 network ${GW_IP}/32

EOF

service quagga restart || true

echo 1 >/proc/sys/net/ipv4/ip_forward

route add -net 10.0.0.0/8 gw ${ROUTER_IP}

route add -net ${EDGE_NETWORK} gw ${ROUTER_IP}

# ps axufwwww | grep -v grep | grep zebra

# ps axufwwww | grep -v grep | grep bgpd

echo

""" % (
        transfer_overlay_ip,
        transfer_underlay_ip,
        transfer_network,
        metadata.config["edge_network"],
        overlay_bgp_session,
        underlay_bgp_session
    ))

