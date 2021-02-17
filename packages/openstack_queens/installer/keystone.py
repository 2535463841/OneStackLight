import os
import socket
import tempfile
import unittest

import yaml

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager
from tests import test_keystone


CONF = config.CONF
LOG = log.LOG


@manager.register_service('keystone')
class KeystoneCentosInstaller(baseinstaller.OpenstackComponentInstaller):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_password = CONF.keystone.keystoneadmin_db_password
        self.wsgi_conf_path = '/usr/share/keystone/wsgi-keystone.conf'
        utils.run_cmd(['unset', 'OS_AUTH_URL', 'OS_USER_DOMAIN_NAME',
                       'OS_PROJECT_NAME', 'OS_USERNAME',
                       'OS_PROJECT_DOMAIN_NAME'])

    @utils.log_steps
    def update_config_files(self):
        """Update Keystone Config Files
        """
        super().update_config_files()
        LOG.debug('config wsgi')
        link_path = os.path.join('/etc/httpd/conf.d/', 'wsgi-keystone.conf')
        if not os.path.exists(link_path):
            utils.run_cmd(['ln', '-s', self.wsgi_conf_path, '/etc/httpd/conf.d/'])

    def verify(self):
        utils.run_cmd(['unset', 'OS_TOKEN', 'OS_URL'])
        LOG.info("create admin openrc file")

        with open(self.admin_openrc, 'w') as f:
            f.writelines([
                "export OS_USERNAME=admin\n",
                "export OS_PASSWORD={0}\n".format(
                    CONF.keystone.admin_password),
                "export OS_PROJECT_NAME=admin\n",
                "export OS_USER_DOMAIN_NAME=Default\n",
                "export OS_PROJECT_DOMAIN_NAME=Default\n",
                "export OS_AUTH_URL=http://{0}:35357/v3\n".format(self.host),
                "export OS_IDENTITY_API_VERSION=3\n",
            ])
        LOG.info('created admin_openrc: %s', self.admin_openrc)
        LOG.info('unittest output:\n')

        runner = unittest.TextTestRunner(verbosity=2)
        suite = unittest.TestSuite()
        suite.addTests(unittest.makeSuite(test_keystone.TestKeystoneInstall))
        runner.run(suite)

    def db_sync(self):
        super(KeystoneCentosInstaller, self).db_sync()
        status, stdout = utils.run_cmd(
            ['keystone-manage', 'fernet_setup',
             '--keystone-user', 'keystone', '--keystone-group', 'keystone']
        )
        if status != 0:
            raise Exception('fernet_setup failed')

    def create_services(self):
        """Create Services And Endpoints
        """

        with open(self.admin_openrc, 'w') as f:
            f.writelines([
                "export OS_TOKEN={0}\n".format(self.conf['init_admin_token']),
                "export OS_URL=http://{0}:35357/v3\n".format(self.host),
                "export OS_IDENTITY_API_VERSION=3\n",
            ])
        LOG.info('created admin_openrc: %s', self.admin_openrc)
        super(KeystoneCentosInstaller, self).create_services()

    def create_auth_users(self):
        super(KeystoneCentosInstaller, self).create_auth_users()
