ifeq "" "$(NODEPS)"

MIDONET_API_DEPS = zookeeper cassandra

MIDONET_AGENTS_DEPS = $(MIDONET_API_DEPS)

MIDONET_CLIENT_DEPS = midonet_api

TUNNELZONE_DEPS = midonet_cli

BRIDGE_DEPS = midonet_cli tunnelzone

ROUTER_DEPS = midonet_cli bridges

MIDONET_GATEWAY_DEPS = midonet_cli tunnelzone routers

VARNISH_DEPS = midonet_gateways

APPLICATION_DEPS = midonet_agents midonet_api tunnelzone bridges routers midonet_gateways haproxy varnish

endif

