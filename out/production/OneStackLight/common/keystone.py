import os
import socket
import tempfile
import unittest

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager
from tests import test_keystone


CONF = config.CONF
LOG = log.LOG


@manager.register_service('keystone')
class KeystoneCentosInstaller(baseinstaller.BaseCentosInstaller):
    PACKAGES = ['openstack-keystone', 'python2-openstackclient',
                'openstack-selinux', 'openstack-utils', 'httpd', 'mod_wsgi']
    SERVICES = ['httpd']

    @utils.log_steps
    def create_authorization(self):
        """Create Authoriaztion
        """
        status, stdout = utils.run_cmd([
            'keystone-manage', 'bootstrap',
            '--bootstrap-password', self.admin_password,
            '--bootstrap-admin-url', "http://{0}:35357/v3/".format(self.host),
            '--bootstrap-internal-url',
            "http://{0}:5000/v3/".format(self.host),
            '--bootstrap-public-url', "http://{0}:5000/v3/".format(self.host),
            '--bootstrap-region-id', 'RegionOne'
        ])
        if status != 0:
            raise Exception('set keystone bootstrap failed')

    @utils.log_steps
    def init_database(self):
        """ Init Keystone Database
        """
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(
                "CREATE DATABASE IF NOT EXISTS {0};".format(self.dbname),
            )
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('create keystone database failed ')

        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.writelines([
                "GRANT ALL ON {0}.* TO '{1}'@'%' identified by "
                "'{2}';\n".format(self.dbname, self.user, self.password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'localhost' "
                "IDENTIFIED BY '{2}';\n".format(self.dbname, self.user,
                                                self.password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'%' IDENTIFIED BY "
                "'{2}';\n".format(self.dbname, self.user, self.password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'%' IDENTIFIED BY "
                "'{2}';\n".format(self.dbname, self.admin_user,
                                  self.admin_password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'{3}' IDENTIFIED BY "
                "'{2}';\n".format(self.dbname, self.admin_user,
                                  self.admin_password, self.host),
            ])
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('set privileges failed ')

    @utils.log_steps
    def update_database(self):
        """Update Database
        """
        status, stdout = utils.run_cmd(['keystone-manage', 'db_sync'])
        if status != 0:
            raise Exception('sync keystone failed, {0}'.format(stdout))

    def __init__(self):
        super().__init__()
        self.cleanup_resources = ["/var/log/keystone"]
        self.keystone_conf = "/etc/keystone/keystone.conf"
        self.dbname = CONF.keystone.dbname
        self.user = CONF.keystone.keystone_db_user
        self.password = CONF.keystone.keystone_db_password
        self.admin_user = CONF.keystone.keystoneadmin_db_user
        self.admin_password = CONF.keystone.keystoneadmin_db_password
        self.conf_path = '/usr/share/keystone/wsgi-keystone.conf'

    @utils.log_steps
    def update_config_files(self):
        """Update Keytone Config Files
        """
        LOG.info('config wsgi')
        link_path = os.path.join('/etc/httpd/conf.d/', 'wsgi-keystone.conf')
        if not os.path.exists(link_path):
            utils.run_cmd(['ln', '-s', self.conf_path, '/etc/httpd/conf.d/'])
        LOG.info('update keystone config')
        utils.openstack_config_set(
            self.keystone_conf,
            'database', 'connection',
            'mysql://{0}:{1}@{2}/{3}'.format(self.admin_user,
                                             self.admin_password,
                                             self.host, self.dbname)
        )

    @utils.log_steps
    def clean_up(self):
        """Clean Up Keystone Files
        """
        utils.rm_path(self.cleanup_resources)

    def verify(self):
        LOG.info("create admin openrc file")

        with open(admin_openrc, 'w') as f:
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
        LOG.info('created admin_openrc: %s', admin_openrc)
        LOG.info('unittest output:\n')

        runner = unittest.TextTestRunner(verbosity=2)
        suite = unittest.TestSuite()
        suite.addTests(unittest.makeSuite(test_keystone.TestKeystoneInstall))
        runner.run(suite)
