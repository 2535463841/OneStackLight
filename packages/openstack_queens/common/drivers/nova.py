import os
from common import config
from common import log
from common import utils
from common import baseinstaller
from common.drivers import base


CONF = config.CONF
LOG = log.LOG


@baseinstaller.register_service('nova')
class NovaCentosInstallDriver(base.OpenstackSerivceDriver):

    def __init__(self, serices_conf):
        super().__init__('nova', serices_conf)

    def init_before_start_services(self):
        nova_conf_dir = os.path.join('/', 'etc', 'nova')
        nova_log_dir = os.path.join('/', 'var', 'log', 'nova')
        LOG.debug(nova_log_dir)
        for path in [nova_conf_dir, nova_log_dir]:
            if not os.path.exists(path):
                os.makedirs(path)
            self.executor.chown.execute(['nova:nova', '-R', path])


@baseinstaller.register_service('nova-compute')
class NovaCentosInstallDriver(base.OpenstackSerivceDriver):

    def __init__(self, serices_conf):
        super().__init__('nova-compute', serices_conf)

    def init_before_start_services(self):
        nova_conf_dir = os.path.join('etc', 'nova')
        nova_log_dir = os.path.join('var', 'log', 'nova')
        for path in [nova_conf_dir, nova_log_dir]:
            if not os.path.exists(path):
                os.makedirs(path)
            self.executor.chown.execute(['nova:nova', '-R', path])
