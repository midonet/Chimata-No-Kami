
    cuisine.package_ensure("haproxy")

    run("""

cat >/etc/default/haproxy<<EOF
ENABLED=1
#EXTRAOPTS="-de -m 16"
EOF

cat >/etc/haproxy/haproxy.cfg<<EOF
global
        log /dev/log    local0
        log /dev/log    local1 notice
        chroot /var/lib/haproxy
        user haproxy
        group haproxy
        daemon

defaults
        retries 3
        maxconn 5000
        log     global
        mode    http
        option  httplog
        option  dontlognull
        contimeout 50000
        clitimeout 500000
        srvtimeout 500000
        errorfile 400 /etc/haproxy/errors/400.http
        errorfile 403 /etc/haproxy/errors/403.http
        errorfile 408 /etc/haproxy/errors/408.http
        errorfile 500 /etc/haproxy/errors/500.http
        errorfile 502 /etc/haproxy/errors/502.http
        errorfile 503 /etc/haproxy/errors/503.http
        errorfile 504 /etc/haproxy/errors/504.http

EOF
""")

    run("""
TYPE="http"
PORT="80"

cat >>/etc/haproxy/haproxy.cfg<<EOF
#
# begin of configuration for ${TYPE}:${PORT}
#
frontend ${TYPE}_${PORT}_frontend
    bind *:${PORT}
    mode http
    default_backend ${TYPE}_${PORT}_backend
    timeout http-keep-alive 500
    timeout http-request 50000

backend ${TYPE}_${PORT}_backend
    mode http
    balance roundrobin
EOF

""")

    idx = 0

    for server in metadata.servers:
        if server in metadata.roles['varnish']:
            idx = idx + 1

            run("""
SERVER_IP="%s"
IDX="%s"

TYPE="http"
PORT="80"

cat >>/etc/haproxy/haproxy.cfg<<EOF
    server ${TYPE}_${PORT}_server${IDX} ${SERVER_IP}:${PORT} check
EOF

""" % (metadata.servers[server]['ip'], idx))

    run("""

service haproxy restart

ps axufwwww | grep -v grep | grep haproxy

""")
