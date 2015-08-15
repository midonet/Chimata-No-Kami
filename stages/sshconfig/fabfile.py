
#
# this code is special, it will not get the code generators .HEAD and .TAIL
#

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

import os

import sys

from chimata.config import Config

from fabric.api import env,parallel,roles,run,local
from fabric.colors import red,yellow,green
from fabric.utils import puts

metadata = Config(os.environ["CONFIGFILE"])

@roles('sshconfig')
def sshconfig():

    puts(green("creating local ssh config for %s" % env.host_string))

    #
    # header
    #

    local("""
TMPDIR="%s"
HOSTNAME="%s"

cat >"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
######################################################################################################################################################################
#
# ssh config fragment ${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt
#
######################################################################################################################################################################

EOF
""" % (
    os.environ["TMPDIR"],
    env.host_string
    ))

    #
    # server config
    #

    local("""
TMPDIR="%s"
HOSTNAME="%s"
DOMAIN="%s"
IP="%s"

cat >>"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
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

    for role in metadata.roles:
        if env.host_string in metadata.roles[role]:
            local("""
TMPDIR="%s"
HOSTNAME="%s"
DOMAIN="%s"
ROLE="%s"
IP="%s"

cat >>"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
#
# ssh config for role ${ROLE} on server ${HOSTNAME} (${IP})
#
Host ${HOSTNAME}_${ROLE}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

Host ${HOSTNAME}.${DOMAIN}_${ROLE}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

Host ${ROLE}_${HOSTNAME}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

Host ${ROLE}_${HOSTNAME}.${DOMAIN}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

Host ${ROLE}.${HOSTNAME}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname ${IP}

Host ${ROLE}.${HOSTNAME}.${DOMAIN}
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
        role,
        metadata.servers[env.host_string]['ip']
    ))

    #
    # application containers via midonet gateways
    #

    if 'applications' in metadata.servers[env.host_string]:
        for application in sorted(metadata.servers[env.host_string]['applications']):
            for container in sorted(metadata.servers[env.host_string]['applications'][application]):
                container_ip = metadata.servers[env.host_string]['applications'][application][container]['ip']

                gwcount = 0

                for midonet_gateway in metadata.roles['midonet_gateways']:
                    gwcount = gwcount + 1

                    #
                    # reach the containers via the midonet gw
                    #

                    local("""
TMPDIR="%s"
SERVER="%s"
HOSTNAME="${SERVER}"
DOMAIN="%s"
SERVER_IP="%s"
GATEWAY_IP="%s"
APPLICATION="%s"
CONTAINER="%s"
CONTAINER_IP="%s"
GWCOUNT="%i"

cat >>"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
#
# ssh config for application container ${APPLICATION}/${CONTAINER} (${CONTAINER_IP}) on ${HOSTNAME} (${SERVER_IP}) via midonet gw ${GATEWAY_IP} (gw ${GWCOUNT})
#
Host ${HOSTNAME}_${APPLICATION}_${CONTAINER}_via_${GATEWAY_IP}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    ProxyCommand /usr/bin/ssh -F${TMPDIR}/.ssh/config -W${CONTAINER_IP}:22 root@${GATEWAY_IP}

Host ${HOSTNAME}_${APPLICATION}_${CONTAINER}.${DOMAIN}_via_${GATEWAY_IP}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    ProxyCommand /usr/bin/ssh -F${TMPDIR}/.ssh/config -W${CONTAINER_IP}:22 root@${GATEWAY_IP}

EOF

""" % (
        os.environ["TMPDIR"],
        env.host_string,
        metadata.config['domain'],
        metadata.servers[env.host_string]['ip'],
        metadata.servers[midonet_gateway]['ip'],
        application,
        container,
        container_ip,
        gwcount
    ))

                    #
                    # reach the containers via the first midonet gw
                    #
                    if gwcount == 1:
                        local("""
TMPDIR="%s"
SERVER="%s"
HOSTNAME="${SERVER}"
DOMAIN="%s"
SERVER_IP="%s"
GATEWAY_IP="%s"
APPLICATION="%s"
CONTAINER="%s"
CONTAINER_IP="%s"

cat >>"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
#
# ssh config for application container ${APPLICATION}/${CONTAINER} (${CONTAINER_IP}) on ${HOSTNAME} (${SERVER_IP})
#
Host ${HOSTNAME}_${APPLICATION}_${CONTAINER}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    ProxyCommand /usr/bin/ssh -F${TMPDIR}/.ssh/config -W${CONTAINER_IP}:22 root@${GATEWAY_IP}

Host ${HOSTNAME}_${APPLICATION}_${CONTAINER}.${DOMAIN}
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    ProxyCommand /usr/bin/ssh -F${TMPDIR}/.ssh/config -W${CONTAINER_IP}:22 root@${GATEWAY_IP}

EOF

""" % (
        os.environ["TMPDIR"],
        env.host_string,
        metadata.config['domain'],
        metadata.servers[env.host_string]['ip'],
        metadata.servers[midonet_gateway]['ip'],
        application,
        container,
        container_ip
    ))

    #
    # footer
    #

    local("""
TMPDIR="%s"
HOSTNAME="%s"

cat >>"${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt" <<EOF
######################################################################################################################################################################
#
# end of ssh config fragment ${TMPDIR}/.ssh/.config.fragment.${HOSTNAME}.txt
#
######################################################################################################################################################################


EOF
""" % (
    os.environ["TMPDIR"],
    env.host_string
    ))

