
    cuisine.package_ensure("docker.io")

    puts(green("installing MidoNet cli on %s" % env.host_string))

    args = {}

    Puppet.apply('midonet::midonet_cli', args, metadata)

    run("""

cat >/root/.midonetrc <<EOF
[cli]
api_url = http://%s:8080/midonet-api
username = admin
password = admin
project_id = admin
tenant = admin
EOF

""" % metadata.servers[metadata.roles['midonet_api'][0]]['ip'])

    server = env.host_string

    run("docker ps")

    run("docker images")

    dockerfile = "/tmp/Dockerfile_chimata_%s" % server

    cuisine.file_write(dockerfile,
"""

#
# chimata base image for all containers running applications
#
# VERSION               0.1.0
#

FROM ubuntu:14.04

RUN rm -rf /var/lib/apt/lists
RUN mkdir -p /var/lib/apt/lists/partial
RUN apt-get clean
RUN apt-get autoclean
RUN apt-get update 1>/dev/null
RUN DEBIAN_FRONTEND=noninteractive apt-get -y -u dist-upgrade 1>/dev/null

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server screen nginx
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN mkdir -pv /var/run/screen
RUN chmod 0777 /var/run/screen

RUN chmod 0755 /usr/bin/screen
RUN mkdir -pv /var/run/sshd

RUN echo 'LANG="en_US.UTF-8"' | tee /etc/default/locale
RUN locale-gen en_US.UTF-8

RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

RUN mkdir -pv /root/.ssh
RUN chmod 0755 /root/.ssh

COPY /root/.ssh/authorized_keys /root/.ssh/authorized_keys
COPY /etc/apt/sources.list /etc/apt/sources.list

ENV NOTVISIBLE "in users profile"

RUN echo "export VISIBLE=now" >> /etc/profile

RUN sync

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]

""")

    #
    # download the container base image and prepare it
    #
    run("""

SERVER_NAME="%s"
DOCKERFILE="/tmp/Dockerfile_chimata_${SERVER_NAME}"

cd "$(mktemp -d)"

cp "${DOCKERFILE}" Dockerfile

mkdir -pv root/.ssh
cat /root/.ssh/authorized_keys >root/.ssh/authorized_keys

mkdir -pv etc/apt
cat /etc/apt/sources.list >etc/apt/sources.list

docker images | grep "template_${SERVER_NAME}" || docker build --no-cache=true -t "template_${SERVER_NAME}" .

""" % server)

    for application in sorted(metadata.servers[server]['applications']):
        for container in sorted(metadata.servers[server]['applications'][application]):

            container_network = metadata.servers[server]['applications'][application][container]['network']
            container_ip = metadata.servers[server]['applications'][application][container]['ip']
            container_gw = metadata.servers[server]['applications'][application][container]['gw']
            container_br = metadata.servers[server]['applications'][application][container]['br']

            container_name = "%s_%s_%s" % (server, application, container)

            namespace_name = "%s_%s" % (application, container)

            puts(green("starting container %s" % container_name))

            #
            # start the container
            #
            run("""
SERVER_NAME="%s"
RUN="%s"

if [[ "" == "$(ps axufwwwwwwwwwwwwwww | grep -v grep | grep -v SCREEN | grep -- "docker run -h ${RUN}")" ]]; then
    screen -d -m -- \
        docker run \
            -h "${RUN}" \
            --privileged=true -i -t --rm --net="none" \
            --name "${RUN}" \
                "template_${SERVER_NAME}"
fi

for i in $(seq 1 120); do
    CONTAINER_ID="$(docker ps | grep "${RUN}" | awk '{print $1;}')"

    if [[ "" == "${CONTAINER_ID}" ]]; then
        sleep 1
    else
        break
    fi
done

if [[ "" == "${CONTAINER_ID}" ]]; then
    echo "container failed to spawn."
    exit 1
fi

CONTAINER_PID="$(docker inspect -f '{{.State.Pid}}' "${CONTAINER_ID}")"

if [[ "${CONTAINER_PID}" == "" ]]; then
    echo "container failed to spawn."
    exit 1
fi

echo "${CONTAINER_PID}:${CONTAINER_ID}"

""" % (server, container_name))

            puts(green("wiring container %s: network: %s ip: %s gw: %s (MTU: %s)" % (
                container_name,
                container_network,
                container_ip,
                container_gw,
                str(metadata.config["overlay_mtu"])
                )))

            #
            # wire the container to a veth pair
            #
            run("""
SERVER_NAME="%s"
NS="%s"
RUN="%s"
NETWORK="%s"
IP="%s"
GW="%s"
OVERLAY_MTU="%s"

CONTAINER_ID="$(docker ps | grep "${RUN}" | awk '{print $1;}')"
CONTAINER_PID="$(docker inspect -f '{{.State.Pid}}' "${CONTAINER_ID}")"

mkdir -p "/var/run/netns"
ln -s "/proc/${CONTAINER_PID}/ns/net" "/var/run/netns/${NS}"

ip link show | grep "${NS}_a" || ip link add "${NS}_a" type veth peer name "${NS}_b"

ip link set "${NS}_a" up
ip link set dev "${NS}_a" mtu "${MTU_CONTAINER}"

ip link show | grep "${NS}_b" && ip link set "${NS}_b" netns "${NS}"

ip netns exec "${NS}" ip link set lo up
ip netns exec "${NS}" ip link set dev "${NS}_b" name eth0
ip netns exec "${NS}" ip link set eth0 up
ip netns exec "${NS}" ip addr add "${IP}/255.255.255.252" dev eth0
ip netns exec "${NS}" ip route add default via "${GW}"
ip netns exec "${NS}" ip link set dev eth0 mtu "${OVERLAY_MTU}"

ip a

ip netns exec "${NS}" ip a

""" % (
    server,
    namespace_name,
    container_name,
    container_network,
    container_ip,
    container_gw,
    str(metadata.config["overlay_mtu"])
    ))

            #
            # wire the container to the datapath in the overlay
            #
            run("""
SERVER_NAME="%s"
NS="%s"
BRIDGE="%s"

for i in $(seq 1 600); do
    midonet-cli -e 'host list' | grep "name ${SERVER_NAME} alive true" && break
    sleep 1
done

BRIDGE="$(midonet-cli -e 'bridge list' | grep "${BRIDGE}" | head -n1 | awk '{print $2;}')"
HOSTID="$(midonet-cli -e 'host list' | grep "name ${SERVER_NAME} alive true" | head -n1 | awk '{print $2;}')"

if [[ "" == "${BRIDGE}" ]]; then
    echo "could not get bridge id from midonet cli"
    exit 1
fi

if [[ "" == "${HOSTID}" ]]; then
    echo "could not get host id from midonet cli"
    exit 1
fi

PORTID="$(midonet-cli -e "bridge ${BRIDGE} port create")"

if [[ "" == "${PORTID}" ]]; then
    echo "failed to create port on bridge, something is wrong - breaking out of loop"
    exit 1
fi

midonet-cli -e "host ${HOSTID} add binding port bridge ${BRIDGE} port ${PORTID} interface ${NS}_a"

echo

""" % (
    server,
    namespace_name,
    container_name
    ))
