import os

import yaml

from common import manager
from common import baseinstaller


@manager.register_service('memcached')
class MemcachedCentosInstaller(baseinstaller.BaseCentosInstaller):

    def __init__(self):
        super().__init__()
        with open(os.path.join('config', 'services.yml')) as f:
            self.conf = yaml.load(f, Loader=yaml.Loader).get('memcached')
