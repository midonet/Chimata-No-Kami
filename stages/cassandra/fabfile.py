
    puts(green("installing cassandra on %s" % env.host_string))

    cs = []

    for cshost in metadata.roles['cassandra']:
        cs.append("'%s'" % metadata.servers[cshost]['ip'])

    args = {}

    args['seeds'] = "[%s]" % ",".join(cs)
    args['seed_address'] = "'%s'" % metadata.servers[env.host_string]['ip']

    Puppet.apply('midonet::cassandra', args, metadata)

    Daemon.poll('org.apache.cassandra.service.CassandraDaemon', 120)

