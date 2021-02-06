import os
import tempfile
import json

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager

import socket

CONF = config.CONF
LOG = log.LOG


@manager.register_service('cinder')
class CinderCentosInstaller(baseinstaller.BaseCentosInstaller):
    PACKAGES = ['openstack-cinder']
    SERVICES = ['openstack-cinder-api', 'openstack-cinder-scheduler']
    description = "OpenStack Block Storage"

    def create_authorization(self):
        """Create Cinder User
        """
        utils.run_openstack_cmd(
            self.admin_openrc,
            ['user', 'create', '--domain', 'default',
             '--password', self.admin_password, 'cinder'])

    def init_database(self):
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(
                "CREATE DATABASE IF NOT EXISTS {0};".format(self.dbname),
            )
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('create cinder database failed ')
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.writelines([
                "GRANT ALL ON {0}.* TO '{1}'@'%' identified by "
                "'{2}';\n".format(self.dbname, self.user, self.password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'localhost' "
                "IDENTIFIED BY '{2}';\n".format(self.dbname, self.user,
                                                self.password),
                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'%' IDENTIFIED BY "
                "'{2}';\n".format(self.dbname, self.user, self.password),

                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'{3}' IDENTIFIED BY "
                "'{2}';\n".format(self.dbname, self.user,
                                  self.password, self.host),
            ])
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('set privileges failed ')

    @utils.log_steps
    def update_database(self):
        """Update Cinder Database
        """
        status, stdout = utils.run_cmd(
            ['cinder-manage', 'db', 'sync'])
        if status != 0:
            raise Exception('cinder db sync failed')

    @utils.log_steps
    def update_config_files(self):
        """Update Cinder Config Files
        """
        configs = {
            'database': {
                'connection': 'mysql://{0}:{1}@{2}/{3}'.format(
                    self.user, self.password, self.host, self.dbname)
            },
            'DEFAULT': {
                'transport_url': 'rabbit://{0}:{1}@{0}'.format(
                    CONF.amqp.openstack_user, CONF.amqp.openstack_pass,
                    self.host),
                'auth_strategy': 'keystone',
                'my_ip': socket.gethostbyname(self.host)
            },
            'keystone_authtoken':{
                'www_authenticate_uri': "http://{0}:5000".format(self.host),
                'auth_url': "http://{0}:5000".format(self.host),
                'memcached_servers': '{0}:11211'.format(self.host),
                'auth_type': 'password',
                'project_domain_name': 'default',
                'user_domain_name': 'default',
                'project_name': 'service',
                'username': 'cinder',
                'password': self.admin_password,
            },
            'oslo_concurrency': {
                'lock_path': '/var/lib/cinder/tmp'
            }
        }

        for section, opts in configs.items():
            for opt, value in opts.items():
                utils.openstack_config_set(self.cinder_conf,
                                           section, opt, value)

        self.config_cinder()
        self.cinder_db_upgrade()
        self.create_cinder_user()
        self.create_cinder_endpoint()

    @utils.log_steps
    def clean_up(self):
        """Cleanup Resources
        """
        LOG.info('deleting cinder service')
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc, ['service', 'list', '-f', 'json'])
        for service in json.loads(stdout):
            if service.get('Name') not in ['cinderv2', 'cinderv3']:
                continue
            LOG.info('delete service %s', service.get('ID'))
            utils.run_openstack_cmd(self.admin_openrc,
                                    ['service', 'delete', service.get('ID')])

        LOG.info('deleting cinder endpoint')
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc, ['endpoint', 'list', '-f', 'json'])

        for endpoint in json.loads(stdout):
            if endpoint.get("Service Name") not in ['cinderv2', 'cinderv3']:
                continue
            LOG.info('delete endpoint %s', endpoint.get('ID'))
            utils.run_openstack_cmd(self.admin_openrc,
                                    ['endpoint', 'delete', endpoint.get('ID')]
            )
        utils.rm_path(self.cleanup_resources)

        LOG.info('deleting cinder user')
        utils.run_openstack_cmd(
            self.admin_openrc, ['user', 'delete', 'cinder'])

    def __init__(self):
        super().__init__()
        self.cinder_conf = "/etc/cinder/cinder.conf"
        self.cleanup_resources = []
        self.dbname = CONF.cinder.dbname
        self.user = CONF.cinder.cinder_db_user
        self.password = CONF.cinder.cinder_db_pass
        self.admin_password = CONF.cinder.admin_password

        base_url = 'http://{0}:8776'.format(self.host)
        self.endpoints_v2 = [
            ('public', '{0}/v2/%(project_id)s'.format(base_url)),
            ('internal', '{0}/v2/%(project_id)s'.format(base_url)),
            ('admin', '{0}/v2/%(project_id)s'.format(base_url))
        ]
        self.endpoints_v3 = [
            ('public', '{0}/v3/%(project_id)s'.format(base_url)),
            ('internal', '{0}/v3/%(project_id)s'.format(base_url)),
            ('admin', '{0}/v3/%(project_id)s'.format(base_url))
        ]

        self.admin_openrc = os.path.join(os.path.expanduser('~'),
                                         'admin_openrc')

    @utils.log_steps
    def create_cinder_endpoint(self):
        """Create Cinder Endpoint
        """
        LOG.info('create cinder service')
        for name, service_type, endpoints in [
            ('cinderv2', 'volumev2', self.endpoints_v2),
            ('cinderv3', 'volumev3', self.endpoints_v3)]:
            self.create_service(service_type, name,
                                description=self.description)

            for interface, url in endpoints:
                self.create_endpoint(name, interface, url)
