import os
from sys import path
import tempfile
import json

import yaml
import shutil

from common import config
from common import log
from common import utils
from common.drivers import base
from common import baseinstaller

import socket

CONF = config.CONF
LOG = log.LOG


@baseinstaller.register_service('neutron')
class NeutronCentosInstaller(base.OpenstackSerivceDriver):

    def __init__(self, serices_conf):
        super().__init__('neutron', serices_conf)

    def update_config_files(self):
        """Update_cnfig_files
        """
        super(NeutronCentosInstaller, self).update_config_files()
        if not os.path.exists('/etc/neutron/plugin.ini'):
            os.symlink('/etc/neutron/plugins/ml2/ml2_conf.ini',
                    '/etc/neutron/plugin.ini')
        
        for d in ['/etc/neutron/conf.d/common', '/var/log/neutron']:
            if not os.path.exists(d):
                os.makedirs(d)
            shutil.chown(d, user='neutron', group='neutron')
