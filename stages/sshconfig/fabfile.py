    puts(green("creating local ssh config for %s" % env.host_string))

    local("""
TMPDIR="%s"
HOSTNAME="%s"
DOMAIN="%s"
IP="%s"

cat >"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
#
# ssh config for server ${HOSTNAME} (${IP})
#
Host ${HOSTNAME}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

Host ${HOSTNAME}.${DOMAIN}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

EOF

""" % (
        os.environ["TMPDIR"],
        env.host_string,
        metadata.config['domain'],
        metadata.servers[env.host_string]['ip']
    ))

