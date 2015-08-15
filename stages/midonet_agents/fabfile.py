
    puts(green("installing MidoNet agent on %s" % env.host_string))

    zk = []

    for zkhost in metadata.roles['zookeeper']:
        zk.append("{'ip' => '%s', 'port' => '2181'}" % metadata.servers[zkhost]['ip'])

    cs = []

    for cshost in metadata.roles['cassandra']:
        cs.append("'%s'" % metadata.servers[cshost]['ip'])

    args = {}

    args['zk_servers'] = "[%s]" % ",".join(zk)
    args['cassandra_seeds'] = "[%s]" % ",".join(cs)

    Puppet.apply('midonet::midonet_agent', args, metadata)

