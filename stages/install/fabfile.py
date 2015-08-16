    puts(yellow("installing packages and configuring server [%s]" % env.host_string))

    #
    # prepare the box
    #
    run("""
NAMESERVER="%s"

DOMAIN="%s"
HOST="%s"

UNDERLAY_MTU="%s"

echo "nameserver ${NAMESERVER}" > /etc/resolv.conf

yes | dpkg --configure -a
yes | apt-get update 1>/dev/null
yes | DEBIAN_FRONTEND=noninteractive apt-get -y -u dist-upgrade 1>/dev/null

for PKG in puppet htop vim screen atop tcpdump nload make git dstat bridge-utils openjdk-7-jre-headless iperf iperf3 traceroute mosh python minicom strace; do
    dpkg -l "${PKG}" | grep "ii  ${PKG}" || \
        yes | DEBIAN_FRONTEND=noninteractive apt-get -q --yes -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" install -- "${PKG}" || true
done

puppet module list 2>/dev/null | grep midonet-midonet || puppet module install midonet-midonet

# patch the datastax key id to avoid the pesky warning
sed -i "s|key        => 'B999A372',|key        => '7E41C00F85BFC1706C4FFFB3350200F2B999A372',|g;" /etc/puppet/modules/midonet/manifests/repository/ubuntu.pp

mkdir -pv /etc/puppet
touch /etc/puppet/hiera.yaml

echo "${HOST}" > /etc/hostname

hostname "${HOST}"

cat >/etc/hosts<<EOF
127.0.0.1 localhost.localdomain localhost
127.0.0.1 $(hostname).${DOMAIN} $(hostname)

# The following lines are desirable for IPv6 capable hosts
::1 ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
EOF

#
# MTU
#
ip link set dev eth0 mtu ${UNDERLAY_MTU} || echo
ip link set dev eth1 mtu ${UNDERLAY_MTU} || echo

exit 0

""" % (
        metadata.config["nameserver"],
        metadata.config["domain"],
        env.host_string,
        metadata.config["underlay_mtu"]
    ))

    #
    # MEM
    #
    if "OS_MIDOKURA_REPOSITORY_USER" in os.environ:
        user = os.environ["OS_MIDOKURA_REPOSITORY_USER"]
        password = os.environ["OS_MIDOKURA_REPOSITORY_PASS"]

        apt = "http://%s:%s@apt.midokura.com" % (user, password)

        run("""
APT="%s"

KEY="${APT}/packages.midokura.key"

wget -SO- "${KEY}" 2>/dev/null | /usr/bin/apt-key add -

wget -SO- "${KEY}" 2>&1

""" % apt)

