import os

import yaml

from common import manager
from common import baseinstaller


@manager.register_service('memcached')
class MemcachedCentosInstaller(baseinstaller.BaseCentosInstaller):
    pass
