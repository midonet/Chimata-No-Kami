
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

