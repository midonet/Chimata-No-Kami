
    puts(green("installing zookeeper on %s" % env.host_string))

    run("""

service zookeeper stop || echo

rm -rf /etc/zookeeper || echo
rm -rf /var/lib/zookeeper || echo

apt-get -y --purge remove zookeeper </dev/null || echo

""")

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

    run("""

mkdir -pv /etc/zookeeper

ln -sf /etc/zookeeper /etc/zookeeper/conf

cat >/etc/zookeeper/conf/environment <<EOF
NAME=zookeeper
ZOOCFGDIR=/etc/zookeeper/conf

CLASSPATH="/etc/zookeeper/conf:/usr/share/java/jline.jar:/usr/share/java/log4j-1.2.jar:/usr/share/java/xercesImpl.jar:/usr/share/java/xmlParserAPIs.jar:/usr/share/java/netty.jar:/usr/share/java/slf4j-api.jar:/usr/share/java/slf4j-log4j12.jar:/usr/share/java/zookeeper.jar"

ZOOCFG="/etc/zookeeper/conf/zoo.cfg"
ZOO_LOG_DIR=/var/log/zookeeper
USER=zookeeper
GROUP=zookeeper
PIDDIR=/var/run/zookeeper
PIDFILE=/var/run/zookeeper/zookeeper.pid
SCRIPTNAME=/etc/init.d/zookeeper
JAVA=/usr/bin/java
ZOOMAIN="org.apache.zookeeper.server.quorum.QuorumPeerMain"
ZOO_LOG4J_PROP="INFO,ROLLINGFILE"
JMXLOCALONLY=false
JAVA_OPTS=""
EOF

chown -R zookeeper:zookeeper /etc/zookeeper || true

""")

    Puppet.apply('midonet::zookeeper', args, metadata)

    Daemon.poll('org.apache.zookeeper.server.quorum', 60)

    for zkhost in sorted(metadata.roles['zookeeper']):
        run("""
IP="%s"
echo ruok | nc "${IP}" 2181 | grep imok
""" % metadata.servers[zkhost]['ip'])

