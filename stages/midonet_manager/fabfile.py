
    if "OS_MIDOKURA_REPOSITORY_USER" in os.environ:
        puts(green("installing MidoNet Manager on %s" % env.host_string))

        run("""
API_IP="%s"
dpkg --configure -a
apt-get install -y -u midonet-manager

#
# midonet manager 1.9.3
#
cat >/var/www/html/midonet-manager/config/client.js <<EOF
{
  "api_host": "http://${API_IP}:8080",
  "login_host": "http://${API_IP}:8080",
  "api_namespace": "midonet-api",
  "api_version": "1.9",
  "api_token": false,
  "poll_enabled": true,
  "agent_config_api_host": "http://${API_IP}:8459",
  "agent_config_api_namespace": "conf",
  "trace_api_host": "http://${API_IP}:8080",
  "traces_ws_url": "ws://${API_IP}:8460"
}
EOF

service apache2 restart

""" % metadata.servers[metadata.roles['midonet_api'][0]]['ip'])

    else:
        puts(yellow("MidoNet Manager is only available in MEM"))

