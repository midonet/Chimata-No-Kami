
    puts(green("installing MidoNet cli on %s" % env.host_string))

    args = {}

    Puppet.apply('midonet::midonet_cli', args, metadata)

    run("""

cat >/root/.midonetrc <<EOF
[cli]
api_url = http://%s:8080/midonet-api
username = admin
password = admin
project_id = admin
tenant = admin
EOF

""" % metadata.servers[metadata.roles['midonet_api'][0]]['ip'])

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


    #
    # set the cassandra hosts
    #

    cshosts = []

    for cshost in sorted(metadata.roles["cassandra"]):
        cshosts.append("%s:9042" % metadata.servers[cshost]["ip"])

    run("""
CSHOSTS="%s"
CSCOUNT="%i"

cat >/tmp/cassandra.json<<EOF
cassandra {
    servers = "${CSHOSTS}"
    replication_factor = ${CSCOUNT}
    cluster = midonet
}

EOF

mn-conf set -t default < /tmp/cassandra.json

""" % (
    ",".join(cshosts),
    len(cshosts)
    ))


    #
    # Puppet bug. *sigh*
    #
    run("""

grep -v '^opyright 2014 Midokura SARL' /etc/midolman/midolman.conf >/etc/midolman/midolman.conf.NEW

mv /etc/midolman/midolman.conf.NEW /etc/midolman/midolman.conf

""")

    run("""

ps axufwwwwwwwwwwwww | grep -v grep | grep 'openjdk' | grep '/etc/midolman/midolman.conf' | grep -v wdog | grep 'midolman' && exit 0

sleep 2

service midolman start

for i in $(seq 1 120); do
    ps axufwwwwwwwwwwwww | grep -v grep | grep -v 'wdog' | grep 'openjdk' | grep '/etc/midolman/midolman.conf' | grep 'midolman' && exit 0
    sleep 1
done

exit 1

""")

    #
    # check if the host made it into zookeeper and is alive, perform cardio-pulmonary reuscitation a bit if its not alive but in zk
    #
    run("""

SERVER="%s"

for i in $(seq 1 600); do

    midonet-cli -e 'host list' | grep "name ${SERVER} alive true" && exit 0

    midonet-cli -e 'host list' | grep "name ${SERVER} alive false" && \
    ( \
        service midolman restart; \
        for i in $(seq 1 240); do \
            echo '.performing CPR - please wait.'; \
            midonet-cli -e 'host list' | grep "name ${SERVER} alive true" && exit 0; \
            sleep 1; \
        done \
    )

    echo '.'

    sleep 2
done

echo

exit 1

""" % env.host_string)

