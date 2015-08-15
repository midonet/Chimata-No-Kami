
    run("""
midonet-cli -e 'tunnel-zone list' | grep 'alexzone' || midonet-cli -e 'tunnel-zone create name alexzone type gre'
""")

    servers = []

    for server in metadata.roles['midonet_agents']:
        servers.append(server)

    for server in servers:
        run("""
HOST="%s"
IP="%s"

ZONE="$(midonet-cli -e 'tunnel-zone list' | grep 'alexzone' | awk '{print $2;}')"

ID="$(midonet-cli -e 'host list' | grep "name ${HOST} alive true" | awk '{print $2;}')"

if [[ "" == "${ID}" ]]; then
    echo "host ${HOST} not found in midonet, agent not running?"
    exit 1
fi

EXISTS="$(midonet-cli -e "tunnel-zone ${ZONE} member list" | grep "host ${ID} address ${IP}")"

if [[ "" == "${EXISTS}" ]]; then
    midonet-cli -e "tunnel-zone ${ZONE} add member host ${ID} address ${IP}"
fi

""" % (server, metadata.servers[server]['ip']))

