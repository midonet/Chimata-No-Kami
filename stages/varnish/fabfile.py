
# TODO varnish config on this host

#sub vcl_fetch {
#        unset beresp.http.x-powered-by;
#        set beresp.grace = 24h;

    director_backends = []
    backends = []

    for server in sorted(metadata.servers):
        if 'applications' in metadata.servers[env.host_string]:
            for application in sorted(metadata.servers[env.host_string]['applications']):
                for container in sorted(metadata.servers[env.host_string]['applications'][application]):
                    container_ip = metadata.servers[env.host_string]['applications'][application][container]['ip']

                    puts(yellow("adding varnish backend %s/%s/%s (%s)" % (server, application, container, container_ip)))

                    director_backends.append("{ .backend = %s_%s_%s; .weight = 10; } " % (server, application, container))

                    #
                    # this hash will be used to write the backends to the vcl later
                    #
                    backends.append("""
backend %s_%s_%s {
    .host                  = "%s";
    .port                  = "80";
    .connect_timeout       = 5s;
    .first_byte_timeout    = 30s;
    .between_bytes_timeout = 30s;
    .max_connections       = 100;
    .saintmode_threshold   = 100;

    .probe = {
                .url       = "/status.php";
                .interval  = 10s;
                .timeout   = 10s;
                .window    = 5;
                .threshold = 3;
    }
}

""" % (
        server,
        application,
        container,
        container_ip
    ))

                #
                # use this string to build the vcl later
                #
                director = "director %s_%s random { %s } " % (env.host_string, application, " ".join(director_backends))

