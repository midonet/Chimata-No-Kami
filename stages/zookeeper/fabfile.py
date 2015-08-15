
    puts(green("installing zookeeper on %s" % env.host_string))

    zk = []

    zkid = 1
    myid = 1

    for zkhost in sorted(metadata.roles['zookeeper']):
        # construct the puppet module params
        zk.append("{'id' => '%s', 'host' => '%s'}" % (zkid, metadata.servers[zkhost]['ip']))

        # are we the current server?
        if env.host_string == zkhost:
            # then this is our id
            myid = zkid

        zkid = zkid + 1

    args = {}

    args['servers'] = "[%s]" % ",".join(zk)
    args['server_id'] = "%s" % myid

    Puppet.apply('midonet::zookeeper', args, metadata)

    Daemon.poll('org.apache.zookeeper.server.quorum', 60)

    for zkhost in sorted(metadata.roles['zookeeper']):
        run("""
IP="%s"
echo ruok | nc "${IP}" 2181 | grep imok
""" % metadata.servers[zkhost]['ip'])

