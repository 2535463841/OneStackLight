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


@manager.register_service('cinder')
class CinderCentosInstaller(baseinstaller.OpenstackComponentInstaller):

    def __init__(self):
        super().__init__()

        with open(os.path.join('config', 'services.yml')) as f:
            self.conf = yaml.load(f, Loader=yaml.Loader).get('cinder')
