#!/usr/bin/python -Werror

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

import re

import os
import sys
import yaml

from fabric.api import *

from fabric.colors import red,yellow,green
from fabric.utils import puts

from netaddr import IPNetwork as CIDR

class Config(object):

    def __init__(self, configfile):
        self._config = self.__set_config(configfile)
        self._roles = self.__set_roles(configfile)
        self._applications = self.__set_applications(configfile)
        self._servers = self.__set_servers(configfile)

        self.__prepare()

        self.__setup_fabric_env()

        if os.environ["DEBUG"] <> "":
            self.__dumpconfig()

    def __dumpconfig(self):
        for role in sorted(self._roles):
            sys.stderr.write("role: %s\n" % role)
        sys.stderr.write("\n")

        for server in self._servers:
            sys.stderr.write("server: %s\n" % server)
            for kv in self._servers[server]:
                sys.stderr.write("__dumpconfig server: [[%s]] - key: [[%s]] - value: [[%s]]\n" % (server, kv, self._servers[server][kv]))

        for server in sorted(self._servers):
            if 'ip' in self._servers[server]:
                sys.stderr.write("server: %s (%s)\n" % (server, self._servers[server]['ip']))
            else:
                sys.stderr.write("ERROR: server %s has no ip property\n" % server)
                sys.exit(1)

            for role in sorted(self._roles):
                if server in self._roles[role]:
                    sys.stderr.write("server role: %s\n" % role)
            sys.stderr.write("\n")

    @classmethod
    def __read_from_yaml(cls, yamlfile, section_name):
        with open(yamlfile, 'r') as yaml_file:
            yamldata = yaml.load(yaml_file.read())

        if yamldata and section_name in yamldata:
            if os.environ["DEBUG"] <> "":
                print
                print yamldata[section_name]
                print
            return yamldata[section_name]
        else:
            return {}

    def __set_config(self, configfile):
        return self.__read_from_yaml(configfile, 'config')

    def __set_roles(self, configfile):
        return self.__read_from_yaml(configfile, 'roles')

    def __set_applications(self, configfile):
        return self.__read_from_yaml(configfile, 'applications')

    def __set_servers(self, configfile):
        return self.__read_from_yaml(configfile, 'servers')

    def __defaults(self):
        defaults = {}

        #
        # at the moment we support random and round-robin in the script stages/varnish/fabfile.py
        #
        defaults["varnish_director_policy"] = "round-robin"
        defaults["varnish_backend_probe_url"] = "/"

        defaults["nameserver"] = "8.8.8.8"
        defaults["parallel"] = True

        defaults["underlay_mtu"] = 1450
        defaults["overlay_mtu"] = 1400

        defaults['container_density'] = 4096

        defaults['basic_roles'] = ['install']

        defaults['no_lock_check'] = ['all_servers', 'sshconfig', 'prune', 'distclean', 'reboot', 'uptime']

        for role in defaults['no_lock_check']:
            defaults['basic_roles'].append(role)

        return defaults

    def __overload_config(self, defaults):
        for overloading_key in defaults:
            if overloading_key not in self._config:
                overloading_value = defaults[overloading_key]
                self._config[overloading_key] = overloading_value

    def __prepare_config(self):
        self.__overload_config(self.__defaults())

    def __check__add_empty_role(self, role):
        if role not in self._roles:
            self._roles[role] = []

    def __prepare_roles(self):

        #
        # midonet_cli server will create the tunnel-zone, bridge and router
        #
        for role in ['tunnelzone', 'bridges', 'routers']:
            self.__check__add_empty_role(role)

            for server in sorted(self._servers):
                if server in self._roles['midonet_cli']:
                    if server not in self._roles[role]:
                        self._roles[role].append(server)

        #
        # each server will create its own sshconfig fragment as a local file in tmp,
        # afterwards a cat will unite these to a .ssh/config in tmp
        #
        for role in self._config['basic_roles']:
            self.__check__add_empty_role(role)

            for server in sorted(self._servers):
                if server not in self._roles[role]:
                    self._roles[role].append(server)

        #
        # varnish nodes will be configured as midonet_gateways, run the agent and will be in the tunnelzone
        #
        for role in ['midonet_gateways', 'midonet_agents']:
            self.__check__add_empty_role(role)

            for server in sorted(self._servers):
                if server in self._roles['varnish']:
                    if server not in self._roles[role]:
                        self._roles[role].append(server)

        #
        # add the application servers as midonet agents and application stage
        #
        for role in ['midonet_agents', 'applications']:
            self.__check__add_empty_role(role)

            for application in self._applications:
                for server in self._applications[application]:
                    if server not in self._roles[role]:
                        self._roles[role].append(server)

    #
    # "Microsegmentation, network virtualization and ghetto IPAM walk into a bar..."
    #
    def __prepare_applications(self):
        application_idx = 0

        for application in sorted(self._applications):
            application_ip_offset = len(self._servers) * self._config['container_density'] * application_idx
            application_idx = application_idx + 1

            server_idx = 0
            for server in sorted(self._applications[application]):
                server_ip_offset = server_idx * self._config['container_density']
                server_idx = server_idx + 1

                self._servers[server]['applications'] = {}
                self._servers[server]['applications'][application] = {}

                container_idx = 0
                for container in sorted(self._applications[application][server]):
                    container_ip_offset = container_idx * 4
                    container_idx = container_idx + 1

                    #
                    # base network for this micro-segment
                    #
                    network_ip_offset = application_ip_offset + server_ip_offset + container_ip_offset

                    gw_ip_offset = network_ip_offset + 1

                    ip_offset = network_ip_offset + 2

                    cproperties = {}

                    cproperties["network"] = CIDR(self._config['overlay'])[network_ip_offset]
                    cproperties["netmask"] = 30

                    cproperties["gw"] = CIDR(self._config['overlay'])[gw_ip_offset]
                    cproperties["ip"] = CIDR(self._config['overlay'])[ip_offset]

                    cproperties["br"] = "%s_%s_%s" % (server, application, container)

                    self._servers[server]['applications'][application][container] = cproperties

    def __prepare_servers(self):
        for role in self._roles:
            for server in self._roles[role]:
                if server not in self._servers:
                    self._servers[server] = {}
                if 'roles' not in self._servers[server]:
                    self._servers[server]['roles'] = []
                if role not in self._servers[server]['roles']:
                    self._servers[server]['roles'].append(role)

        for server in self._servers:
            for global_config_key in self._config:
                if global_config_key not in self._servers[server]:
                    value = self._config[global_config_key]
                    self._servers[server][global_config_key] = value

    def __prepare(self):
        self.__prepare_config()
        self.__prepare_roles()
        self.__prepare_applications()
        self.__prepare_servers()

    def __setup_fabric_env(self):
        env.use_ssh_config = True
        env.port = 22
        env.connection_attempts = 5
        env.timeout = 5
        env.parallel = self._config["parallel"]
        env.roledefs = self._roles

    @property
    def config(self):
        return self._config

    @property
    def roles(self):
        return self._roles

    @property
    def applications(self):
        return self._applications

    @property
    def servers(self):
        return self._servers

