import os
import tempfile
import json

import yaml

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager

import socket

CONF = config.CONF
LOG = log.LOG


@manager.register_service('neutron')
class NeutronCentosInstaller(baseinstaller.OpenstackComponentInstaller):

    def __init__(self):
        super().__init__()

        with open(os.path.join('config', 'services.yml')) as f:
            self.conf = yaml.load(f, Loader=yaml.Loader).get('neutron')

    def update_config_files(self):
        super(NeutronCentosInstaller, self).update_config_files()
        utils.run_cmd(
            ['ln', '-sf', '/etc/neutron/plugins/ml2/ml2_conf.ini',
             '/etc/neutron/plugin.ini']
        )
        for d in ['/etc/neutron/conf.d/common', '/var/log/neutron']:
            utils.run_cmd(['mkdir', d,
                           '&&', 'chown', '-R', 'neutron:neutron', d])
