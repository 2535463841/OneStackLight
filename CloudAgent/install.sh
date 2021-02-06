#!/usr/bin/env bash
# 1. Install CloudAgent to directory "/opt"
# 2. Config cloud-agent.service
# 3. Restart cloud-agent service

PACKAGE_DIR=`pwd`

INSTALL_DIR='/opt'
PACKAGE_NAME='CloudAgent'
SYSTEM_SERVICE_DIR='/usr/lib/systemd/system'

function info() {
    echo 'INFO:' $1
}

function error() {
    echo 'ERROR:' $1
}

function main() {
    systemctl stop cloud-agent
    if [[ $? -ne 0 ]]; then
        error 'stop cloud-agent service failed'
        return 1
    fi
    info 'stop cloud-agent service success'

    rm -rf "${INSTALL_DIR}/${PACKAGE_NAME}"
    cp -r "${PACKAGE_DIR}" "${INSTALL_DIR}"
    if [[ $? -ne 0 ]]; then
        error 'cp CloudAgent package failed!'
        return 1
    fi
    info 'cp CloudAgent package success!'
    cp -r "${PACKAGE_DIR}/config/cloud-agent.service" "${SYSTEM_SERVICE_DIR}"
    if [[ $? -ne 0 ]]; then
        error 'cp cloud-agent.service failed!'
        return 1
    fi
    info 'cp cloud-agent.service success!'

    systemctl daemon-reload
    systemctl start cloud-agent
    if [[ $? -ne 0 ]]; then
        error 'start cloud-agent service failed'
        return 1
    fi
    info 'start cloud-agent service success'

    return 0
}

main

exit $?
