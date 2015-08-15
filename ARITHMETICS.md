ip arithmetics in bash:

ip2dec () {
    local a b c d ip=$@
    IFS=. read -r a b c d <<< "$ip"
    printf '%%d' "$((a * 256 ** 3 + b * 256 ** 2 + c * 256 + d))"
}

dec2ip () {
    local ip dec=$@
    for e in {3..0}
    do
        ((octet = dec / (256 ** e) ))
        ((dec -= octet * 256 ** e))
        ip+=$delim$octet
        delim=.
    done
    printf '%%s' "$ip"
}

# start at ip .20 in the 1024 block
k=20

for i in $(seq "$(( ${k} ))" "$(( ${k} + ${MAXPAIRS} ))"); do
    IP="$(dec2ip $(( $(ip2dec ${FIRST_IP}) + ${k} )))"

    midonet-cli -e "load-balancer ${LB_ID} pool ${POOL_ID} create member address ${IP} protocol-port 80"

    k="$(( ${k} + 1 ))"
done

