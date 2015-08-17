
    run("""
rm -vf /tmp/.chimata_lockfile__*

</dev/null dpkg --configure -a

</dev/null apt-get -f -y install

apt-get -y --purge remove midolman </dev/null

apt-get -y --purge remove midonet-api </dev/null

rm -rf /etc/midolman
rm -rf /var/log/midolman

apt-get -y --purge remove zookeeper </dev/null
apt-get -y --purge remove cassandra </dev/null

service zookeeper stop
service cassandra stop
service quagga stop

rm -rf /etc/cassandra
rm -rf /etc/zookeeper
rm -rf /var/lib/zookeeper

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

