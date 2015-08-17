
    cuisine.package_ensure("expect")

    puts(green("configuring midonet virtual router (using cli on %s)" % env.host_string))

    edge_network = metadata.config["edge_network"]

    #
    # edge router. this is what we usually know as the MidoNet Provider Router
    #
    run("""

ROUTER_IP="%s"
NETWORK="%s"
BRIDGE="bridge_edge"

midonet-cli -e 'router list' | grep 'name router_edge' || midonet-cli -e 'router add name router_edge'

ROUTER_ID="$(midonet-cli -e "router list name router_edge" | awk '{print $2;}')"

#
# create the southbound edge router port for the edge bridge
#
midonet-cli -e "router ${ROUTER_ID} port list" | grep "address ${ROUTER_IP} net ${NETWORK}/24" || \
    midonet-cli -e "router ${ROUTER_ID} add port address ${ROUTER_IP} net ${NETWORK}/24"

#
# hook up the edge router to the southbound edge bridge
#
/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }
expect "midonet> " { send "router list name router_edge\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/24\r" }
expect "midonet> " { send "bridge list name ${BRIDGE}\r" }
expect "midonet> " { send "bridge bridge0 port create\r" }
expect "midonet> " { send "router router0 port port0 set peer bridge0:port0\r" }
expect "midonet> " { send "quit\r" }
EOF

""" % (
        CIDR(edge_network)[1],
        CIDR(edge_network)[0]
    ))

    applications = []

    for server in sorted(metadata.servers):
        if "applications" in metadata.servers[server]:
            for application in sorted(metadata.servers[server]['applications']):
                if application not in applications:
                    applications.append(application)

    idx = 1
    for application in applications:
        idx = idx + 1

        network = CIDR(edge_network)[0]

        downlink = CIDR(edge_network)[idx]

        uplink = CIDR(edge_network)[1]

        run("""

ROUTER="router_%s"

NETWORK="%s"

ROUTER_IP="%s"

GW_IP="%s"

#
# create the application router
#
midonet-cli -e 'router list' | grep "${ROUTER}" || midonet-cli -e "router add name ${ROUTER}"

ROUTER_ID="$(midonet-cli -e "router list name ${ROUTER}" | awk '{print $2;}')"

#
# create the northbound application router port for the edge bridge
#
midonet-cli -e "router ${ROUTER_ID} port list" | grep "address ${ROUTER_IP} net ${NETWORK}/24" || \
    midonet-cli -e "router ${ROUTER_ID} add port address ${ROUTER_IP} net ${NETWORK}/24"

midonet-cli -e "router ${ROUTER_ID} port list" | grep "address ${ROUTER_IP} net ${NETWORK}/24 peer bridge" && exit 0

/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }

expect "midonet> " { send "router list name ${ROUTER}\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/24\r" }
expect "midonet> " { send "router router0 add route src 0.0.0.0/0 dst 0.0.0.0/0 type normal weight 100 port router0:port0 gw ${GW_IP}\r" }

expect "midonet> " { send "bridge list name bridge_edge\r" }
expect "midonet> " { send "bridge bridge0 port create\r" }
expect "midonet> " { send "router router0 port port0 set peer bridge0:port0\r" }

expect "midonet> " { send "quit\r" }
EOF

echo

""" % (
    application,
    network,
    downlink,
    uplink
    ))

        #
        # routing for the micro-segment bridges of the docker containers
        #
        for server in sorted(metadata.servers):
            if "applications" in metadata.servers[server]:
                for application in sorted(metadata.servers[server]['applications']):
                    for container in sorted(metadata.servers[server]['applications'][application]):
                        container_network = metadata.servers[server]['applications'][application][container]['network']

                        #
                        # route this network through this application router
                        #
                        run("""
ROUTER_IP="%s"
NETWORK="%s"
GW_IP="%s"
DESTINATION_NETWORK="%s"

/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }
expect "midonet> " { send "router list name router_edge\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/24\r" }
expect "midonet> " { send "router router0 add route src 0.0.0.0/0 dst ${DESTINATION_NETWORK}/30 type normal weight 100 port router0:port0 gw ${GW_IP}\r" }
expect "midonet> " { send "quit\r" }
EOF

echo

""" % (
        CIDR(edge_network)[1],
        CIDR(edge_network)[0],
        downlink,
        container_network
    ))

    #
    # wire the application routers to the bridges
    #

    for server in sorted(metadata.servers):
        if "applications" in metadata.servers[server]:
            for application in sorted(metadata.servers[server]['applications']):
                for container in sorted(metadata.servers[server]['applications'][application]):
                    container_network = metadata.servers[server]['applications'][application][container]['network']
                    container_ip = metadata.servers[server]['applications'][application][container]['ip']
                    container_gw = metadata.servers[server]['applications'][application][container]['gw']
                    container_br = metadata.servers[server]['applications'][application][container]['br']

                    puts(green("wiring router router_%s with ip %s on network %s to bridge bridge_%s" % (
                        application, container_gw, container_network, container_br)))

                    run("""

ROUTER="router_%s"

ROUTER_IP="%s"

NETWORK="%s"

#
# microsegmentation ftw
#
BRIDGE="bridge_%s"

ROUTER_ID="$(midonet-cli -e "router list name ${ROUTER}" | awk '{print $2;}')"

if [[ "" == "${ROUTER_ID}" ]]; then
    echo "could not find router ${ROUTER}, bailing out"
    exit 1
fi

#
# create the port on the router to link to the bridge
#

midonet-cli -e "router ${ROUTER_ID} port list" | grep "address ${ROUTER_IP} net ${NETWORK}/30" || \
    midonet-cli -e "router ${ROUTER_ID} add port address ${ROUTER_IP} net ${NETWORK}/30"

#
# if the binding is there do not spam ports on the bridge
#
midonet-cli -e "router ${ROUTER_ID} port list" | grep "address ${ROUTER_IP} net ${NETWORK}/30 peer bridge" && exit 0

/usr/bin/expect<<EOF 1>/dev/null 2>/dev/null
set timeout 10
spawn midonet-cli
expect "midonet> " { send "cleart\r" }
expect "midonet> " { send "router list name ${ROUTER}\r" }
expect "midonet> " { send "router router0 port list address ${ROUTER_IP} net ${NETWORK}/30\r" }
expect "midonet> " { send "router router0 add route src 0.0.0.0/0 dst ${NETWORK}/30 type normal weight 100 port router0:port0\r" }
expect "midonet> " { send "bridge list name ${BRIDGE}\r" }
expect "midonet> " { send "bridge bridge0 port create\r" }
expect "midonet> " { send "router router0 port port0 set peer bridge0:port0\r" }
expect "midonet> " { send "quit\r" }
EOF

echo

""" % (
    application,
    container_gw,
    container_network,
    container_br
    ))

