#
# Copyright (c) 2015 Midokura SARL, All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#  __  __ _     _                  _
# |  \/  (_) __| | ___  _ __   ___| |_
# | |\/| | |/ _` |/ _ \| '_ \ / _ \ __|
# | |  | | | (_| | (_) | | | |  __/ |_
# |_|  |_|_|\__,_|\___/|_| |_|\___|\__|
#

DEBUG = $(shell env | grep ^DEBUG)

NODEPS = $(shell env | grep ^NODEPS)

ALLTARGETS = $(PREREQUISITES) install zookeeper cassandra midonet_agents midonet_api midonet_manager midonet_cli tunnelzone bridge router midonet_gateways haproxy varnish applications

all: $(ALLTARGETS)

include include/chimata.mk

include include/dependencies.mk

#
# prepare the machines and install the puppet modules
#
install:          $(PREREQUISITES) $(INSTALL_DEPS)
	$(RUNSTAGE)

#
# install zookeeper, the topology database
#
zookeeper:        $(PREREQUISITES) $(ZOOKEEPER_DEPS)
	$(RUNSTAGE)

#
# install cassandra
#
cassandra:        $(PREREQUISITES) $(CASSANDRA_DEPS)
	$(RUNSTAGE)

#
# install and configure midonet agents on all gateways and veth pair hosts
#
midonet_agents:   $(PREREQUISITES) $(MIDONET_AGENTS_DEPS)
	$(RUNSTAGE)

#
# install and configure midonet api
#
midonet_api:      $(PREREQUISITES) $(MIDONET_API_DEPS)
	$(RUNSTAGE)

#
# install and configure midonet manager
#
midonet_manager:  $(PREREQUISITES) $(MIDONET_CLIENT_DEPS)
	$(RUNSTAGE)

#
# install and configure midonet_cli on all machines
#
midonet_cli:      $(PREREQUISITES) $(MIDONET_CLIENT_DEPS)
	$(RUNSTAGE)

#
# add hosts to tunnel-zone
#
tunnelzone:       $(PREREQUISITES) $(TUNNELZONE_DEPS)
	$(RUNSTAGE)

#
# create a virtual bridge
#
bridge:           $(PREREQUISITES) $(BRIDGE_DEPS)
	$(RUNSTAGE)

#
# create a virtual router, attaches it to the bridge
#
router:           $(PREREQUISITES) $(ROUTER_DEPS)
	$(RUNSTAGE)

#
# configure the router uplinks on the gateways with veth pairs and classic SNAT
#
midonet_gateways: $(PREREQUISITES) $(MIDONET_GATEWAY_DEPS)
	$(RUNSTAGE)

#
# set up the http load balancers
#
haproxy: $(PREREQUISITES) $(HAPROXY_DEPS)
	$(RUNSTAGE)

#
# set up the http caches
#
varnish: $(PREREQUISITES) $(VARNISH_DEPS)s
	$(RUNSTAGE)

#
# set up the nginx in the docker containers
#
applications: $(PREREQUISITES) $(APPLICATION_DEPS)
	$(RUNSTAGE)

prune: $(PREREQUISITES) $(PRUNE_DEPS)
	$(RUNSTAGE)

distclean: $(PREREQUISITES) $(DISTCLEAN_DEPS)
	$(RUNSTAGE)

reboot: $(PREREQUISITES) $(REBOOT_DEPS)
	$(RUNSTAGE)

