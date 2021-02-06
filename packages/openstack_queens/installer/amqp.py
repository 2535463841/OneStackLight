import os
import unittest

import yaml

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager
from tests import test_amqp


CONF = config.CONF
LOG = log.LOG


@manager.register_service('amqp')
class AMQPCentosInstaller(baseinstaller.BaseCentosInstaller):

    def __init__(self):
        super().__init__()
        with open(os.path.join('config', 'services.yml')) as f:
            self.conf = yaml.load(f, Loader=yaml.Loader).get('amqp')

    @utils.log_steps
    def clean_up(self):
        """Clean Up Resources"""
        utils.rm_path(['/var/lib/rabbitmq'])

    @utils.log_steps
    def after_start(self):
        """After Start Services
        """
        if self.conf.get('enable_management'):
            LOG.debug('enable rabbitmq management')
            status, stdout = utils.run_cmd(
                ['rabbitmq-plugins', 'enable', 'rabbitmq_management']
            )
            if status != 0:
                LOG.error('enable rabbitmq management failed')

        init_user = self.conf.get('init_user')
        if init_user:
            utils.run_cmd([
                'rabbitmqctl', 'add_user',
                init_user.get('name'), init_user.get('password')
            ])
            utils.run_cmd([
                'rabbitmqctl', 'set_permissions', '-p', '/',
                init_user.get('name'), '".*" ".*" ".*"'
            ])

    def verify(self):
        runner = unittest.TextTestRunner(verbosity=2)
        suite = unittest.TestSuite()
        suite.addTests(unittest.makeSuite(test_amqp.TestAMQPInstall))
        runner.run(suite)
