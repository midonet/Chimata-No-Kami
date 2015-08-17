    puts(green("configuring midonet virtual switches (using cli on %s)" % env.host_string))

    run("""

midonet-cli -e 'bridge list' | grep 'name bridge_edge' || midonet-cli -e 'bridge add name bridge_edge'

""")

    bridges = []

    for server in sorted(metadata.servers):
        if "applications" in metadata.servers[server]:
            for application in sorted(metadata.servers[server]['applications']):
                for container in sorted(metadata.servers[server]['applications'][application]):
                    bridge = metadata.servers[server]['applications'][application][container]['br']

                    if bridge not in bridges:
                        bridges.append(bridge)

    for bridge in bridges:
        run("""

BRIDGE="bridge_%s"

midonet-cli -e 'bridge list' | grep "${BRIDGE}" || midonet-cli -e "bridge add name ${BRIDGE}"

""" % bridge)

