
    puts(green("installing cassandra on %s" % env.host_string))

    run("""

service cassandra stop || true

apt-get -y --purge remove cassandra </dev/null || true

rm -rf /etc/cassandra || true

rm -rf /var/lib/cassandra || true

mkdir -pv /etc/cassandra

mkdir -pv /var/lib/cassandra

chown -R cassandra:cassandra /var/lib/cassandra || true

""")

    cs = []

    for cshost in metadata.roles['cassandra']:
        cs.append("'%s'" % metadata.servers[cshost]['ip'])

    args = {}

    args['seeds'] = "[%s]" % ",".join(cs)
    args['seed_address'] = "'%s'" % metadata.servers[env.host_string]['ip']

    Puppet.apply('midonet::cassandra', args, metadata)

    Daemon.poll('org.apache.cassandra.service.CassandraDaemon', 120)

