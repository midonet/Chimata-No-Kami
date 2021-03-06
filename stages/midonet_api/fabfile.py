
    puts(green("installing MidoNet api on %s" % env.host_string))

    zk = []

    for zkhost in metadata.roles['zookeeper']:
        zk.append("{'ip' => '%s', 'port' => '2181'}" % metadata.servers[zkhost]['ip'])

    args = {}

    args['zk_servers'] = "[%s]" % ",".join(zk)
    args['keystone_auth'] = "false"
    args['vtep'] = "true"

    if 'fip' in metadata.servers[env.host_string]:
        args['api_ip'] = "'%s'" % metadata.servers[env.host_string]['fip']
    else:
        args['api_ip'] = "'%s'" % metadata.servers[env.host_string]['ip']

    run("""
echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6

apt-get remove --purge -y midonet-api; echo
apt-get remove --purge -y tomcat7; echo
apt-get remove --purge -y tomcat6; echo
""")

    Puppet.apply('midonet::midonet_api', args, metadata)

    run("""

cat >/etc/default/tomcat7 <<EOF
TOMCAT7_USER=tomcat7
TOMCAT7_GROUP=tomcat7
JAVA_OPTS="-Djava.awt.headless=true -Xmx128m -XX:+UseConcMarkSweepGC -Djava.net.preferIPv4Stack=true -Djava.security.egd=file:/dev/./urandom"
EOF

sed -i 's,org.midonet.api.auth.MockAuthService,org.midonet.cluster.auth.MockAuthService,g;' /usr/share/midonet-api/WEB-INF/web.xml

rm -rfv /var/log/tomcat7/*

service tomcat7 restart

""")

