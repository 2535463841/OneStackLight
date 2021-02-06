import unittest

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
    PACKAGES = ['rabbitmq-server']
    SERVICES = ['rabbitmq-server']

    def create_authorization(self):
        pass

    def init_database(self):
        pass

    def update_database(self):
        pass

    def update_config_files(self):
        pass

    @utils.log_steps
    def clean_up(self):
        """Clean Up Resources"""
        utils.rm_path(['/var/lib/rabbitmq'])

    @utils.log_steps
    def after_start(self):
        """After Start Services
        """
        if CONF.amqp.enable_management:
            LOG.info('enable rabbitmq management')
            status, stdout = utils.run_cmd(
                ['rabbitmq-plugins', 'enable', 'rabbitmq_management']
            )
            if status != 0:
                LOG.error('enable rabbitmq management failed')

    def verify(self):
        runner = unittest.TextTestRunner(verbosity=2)
        suite = unittest.TestSuite()
        suite.addTests(unittest.makeSuite(test_amqp.TestAMQPInstall))
        runner.run(suite)
