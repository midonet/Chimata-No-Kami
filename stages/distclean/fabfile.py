
    run("""
rm -vf /tmp/.chimata_lockfile__*

rm -rf /etc/cassandra
rm -rf /etc/zookeeper

rm -fv /etc/haproxy/haproxy.cfg
rm -fv /etc/newrelic/nrsysmond.cfg
rm -fv /etc/apt/sources.list.d/cloudarchive*
rm -fv /etc/apt/sources.list.d/newrelic*
rm -fv /etc/apt/sources.list.d/mido*

iptables -t nat --flush

iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

iptables --flush

""")

