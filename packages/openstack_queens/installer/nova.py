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


@manager.register_service('nova')
class NovaCentosInstaller(baseinstaller.OpenstackComponentInstaller):
    SERVICE_NAME = 'nova'


@manager.register_service('nova-compute')
class NovaCentosInstaller(baseinstaller.OpenstackComponentInstaller):
    SERVICE_NAME = 'nova-compute'
