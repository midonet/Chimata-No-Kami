ifeq "" "$(NODEPS)"

MIDONET_AGENTS_DEPS = zookeeper cassandra

MIDONET_API_DEPS = zookeeper cassandra midonet_agents

MIDONET_CLIENT_DEPS = midonet_api

TUNNELZONE_DEPS = midonet_cli

BRIDGE_DEPS = midonet_cli tunnelzone

ROUTER_DEPS = midonet_cli bridge

MIDONET_GATEWAY_DEPS = midonet_cli tunnelzone router

VARNISH_DEPS = midonet_gateways

APPLICATION_DEPS = midonet_agents midonet_api tunnelzone bridge router midonet_gateways haproxy varnish

endif

