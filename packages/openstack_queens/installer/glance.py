import os

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager

import yaml

CONF = config.CONF
LOG = log.LOG


@manager.register_service('glance')
class GlanceCentosInstaller(baseinstaller.OpenstackComponentInstaller):

    @utils.log_steps
    def update_config_files(self):
        """Update glance Config Files
        """
        super().update_config_files()
        glance_log = '/var/log/glance/api.log'
        if not os.path.exists(glance_log):
            utils.run_cmd(['touch', glance_log])
        utils.run_cmd(['chown', '-R', 'glance:glance', glance_log])
