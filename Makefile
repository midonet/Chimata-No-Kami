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

# DEBUG = xoxo

PREREQUISITES = codegen preflight sshconfig

ALLTARGETS = $(PREREQUISITES) install zookeeper cassandra midonet_agents midonet_api midonet_manager midonet_cli tunnelzone bridge router midonet_gateways haproxy varnish applications

all: $(ALLTARGETS)

include include/chimata.mk

#
# prepare the machines and install the puppet modules
#
install:          $(PREREQUISITES)
	$(RUNSTAGE)

#
# install zookeeper, the topology database
#
zookeeper:        $(PREREQUISITES)
	$(RUNSTAGE)

#
# install cassandra
#
cassandra:        $(PREREQUISITES)
	$(RUNSTAGE)

#
# install and configure midonet agents on all gateways and veth pair hosts
#
midonet_agents:   $(PREREQUISITES) zookeeper cassandra
	$(RUNSTAGE)

#
# install and configure midonet api
#
midonet_api:      $(PREREQUISITES) zookeeper cassandra midonet_agents
	$(RUNSTAGE)

#
# install and configure midonet manager
#
midonet_manager:  $(PREREQUISITES) midonet_api
	$(RUNSTAGE)

#
# install and configure midonet_cli on all machines
#
midonet_cli:      $(PREREQUISITES) midonet_api
	$(RUNSTAGE)

#
# add hosts to tunnel-zone
#
tunnelzone:       $(PREREQUISITES) midonet_cli
	$(RUNSTAGE)

#
# create a virtual bridge
#
bridge:           $(PREREQUISITES) midonet_cli tunnelzone
	$(RUNSTAGE)

#
# create a virtual router, attaches it to the bridge
#
router:           $(PREREQUISITES) midonet_cli bridge
	$(RUNSTAGE)

#
# configure the router uplinks on the gateways with veth pairs and classic SNAT
#
midonet_gateways: $(PREREQUISITES) midonet_cli tunnelzone router
	$(RUNSTAGE)

#
# set up the http load balancers
#
haproxy: $(PREREQUISITES)
	$(RUNSTAGE)

#
# set up the http caches
#
varnish: $(PREREQUISITES) midonet_gateways
	$(RUNSTAGE)

#
# set up the nginx in the docker containers
#
applications: $(PREREQUISITES) midonet_agents midonet_api tunnelzone bridge router midonet_gateways haproxy varnish
	$(RUNSTAGE)

prune: sshconfig
	$(RUNSTAGE)

