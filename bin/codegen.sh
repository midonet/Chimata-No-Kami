#!/bin/bash

SKEL="stages/skel/fabfile.py"

for STAGE in $(make -rpn | \
    sed -n -e '/^$/ { n ; /^[^ ]*:/p }' | \
    grep -v ^all: | \
    grep -v ^pipinstalled: | \
    grep -v ^pipdeps: | \
    grep -v ^clean: | \
    grep -v ^preflight: | \
    grep -v ^codegen: | \
    grep -v 'Chimata-No-Kami/tmp:' | \
    awk '{print $1;}' | \
    sed 's,:,,g' | \
    sort -n | \
    uniq)
do
    FABFILE="stages/${STAGE}/fabfile.py"
    CODE_FRAGMENT="stages/${STAGE}/.fragment.py"

    echo "patching ${FABFILE}"

    mkdir -pv "$(dirname ${FABFILE})"

    #
    # header
    #
    cat "${SKEL}" > "${FABFILE}"

    #
    # role definition for fabric
    #
    cat >> "${FABFILE}"<<EOF
@roles('${STAGE}')
def ${STAGE}():
EOF

    if [[ -f "${CODE_FRAGMENT}" ]]; then
        echo "code fragment found for ${FABFILE}, adding ${CODE_FRAGMENT}"
        <"${FABFILE}" >>"${CODE_FRAGMENT}"
    else
        echo "    pass" >> "${FABFILE}"
    fi

    chmod 0755 "${FABFILE}"
done
