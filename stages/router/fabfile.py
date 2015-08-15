    puts(green("configuring midonet virtual router (using cli on %s)" % env.host_string))

    run("""

midonet-cli -e 'router list' | grep 'name alexrouter' || midonet-cli -e 'router add name alexrouter'

""")

    # TODO create vports with edge network, ip offset is edge base net + 4*current midonet-gw (a /30 for two vports)

