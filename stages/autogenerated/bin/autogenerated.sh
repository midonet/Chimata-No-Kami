#!/bin/bash

SKEL="stages/skel/fabfile.py"

for STAGE in $(make -rpn | \
    sed -n -e '/^$/ { n ; /^[^ ]*:/p }' | \
    grep -v ^all: | \
    grep -v ^pipinstalled: | \
    grep -v ^pipdeps: | \
    grep -v ^clean: | \
    grep -v ^preflight: | \
    grep -v ^autogenerated: | \
    grep -v 'Chimata-No-Kami/tmp:' | \
    awk '{print $1;}' | \
    sed 's,:,,g' | \
    sort -n | \
    uniq)
do
    AUTOGEN="autogenerated/${STAGE}/fabfile.py"
    FABFILE="stages/${STAGE}/fabfile.py"

    echo "patching ${AUTOGEN}"

    mkdir -pv "$(dirname ${AUTOGEN})"
    mkdir -pv "$(dirname ${FABFILE})"

    #
    # code generator head
    #
    cat "${SKEL}.HEAD" >"${AUTOGEN}.HEAD"

    #
    # apply macros in code template
    #
    sed -i 's,%%GENERATOR%%,'"${0}"',g;' "${AUTOGEN}.HEAD"
    sed -i 's,%%ROLE%%,'"${STAGE}"',g;' "${AUTOGEN}.HEAD"

    if [[ ! "sshconfig" == "${STAGE}" ]]; then
        cat "${AUTOGEN}.HEAD" >"${AUTOGEN}"
    fi

    rm "${AUTOGEN}.HEAD"

    #
    # insert hand written fragment code if it exists
    #
    if [[ -f "${FABFILE}" ]]; then
        echo "code fragment found for ${AUTOGEN}, adding ${FABFILE}"

        cat >>"${AUTOGEN}" <<EOF
#
# begin of code fragment from ${FABFILE}
#
EOF
        cat "${FABFILE}" >>"${AUTOGEN}"

        cat >>"${AUTOGEN}" <<EOF
#
# end of code fragment from ${FABFILE}
#
EOF

    else
        echo "    pass" >> "${AUTOGEN}"
    fi

    #
    # code generator tail
    #
    cat "${SKEL}.TAIL" >>"${AUTOGEN}.TAIL"

    #
    # apply macros in code template
    #
    sed -i 's,%%GENERATOR%%,'"${0}"',g;' "${AUTOGEN}.TAIL"
    sed -i 's,%%ROLE%%,'"${STAGE}"',g;' "${AUTOGEN}.TAIL"

    if [[ ! "sshconfig" == "${STAGE}" ]]; then
        cat "${AUTOGEN}.TAIL" >> "${AUTOGEN}"
    fi

    rm "${AUTOGEN}.TAIL"

    chmod 0755 "${AUTOGEN}"
done

