import os
import socket
import tempfile
import json
import yaml
import collections

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

from tqdm import tqdm

from common import utils
from common import log
from common import manager
from common.lib import keystone


LOG = log.LOG


def register_to_yaml_constructor(func):
    LOG.debug('register yaml constructor !%s %s', func.__name__, func)
    yaml.add_constructor('!{0}'.format(func.__name__), func)
    return func


@register_to_yaml_constructor
def string_join(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


@register_to_yaml_constructor
def string_format(loader, node):
    seq = loader.construct_sequence(node)
    LOG.debug('string_format: %s', seq)
    return seq[0] % tuple(seq[1:])


@register_to_yaml_constructor
def get_hostname(loader, node):
    return socket.gethostname()


@register_to_yaml_constructor
def get_host_ip(loader, node):
    return socket.gethostbyname(socket.gethostname())


@register_to_yaml_constructor
def openssl_rand_hex10(loader, node):
    _, stdout = utils.run_cmd(['openssl', 'rand', '-hex', '10'])
    return stdout


class BaseCentosInstaller:
    SERVICE_NAME = None

    def __init__(self):
        self.host = socket.gethostname()
        self.admin_openrc = os.path.join(os.path.expanduser('~'),
                                         'admin_openrc')
        with open(os.path.join('config', 'services.yml')) as f:
            self.installer_conf = yaml.load(f, Loader=yaml.Loader)
        self.conf = self.installer_conf.get(self.SERVICE_NAME)
        if not self.conf:
            raise Exception('conf of {0} is None'.format(self.SERVICE_NAME))
        self.manager = manager.CentosManager()
        self.db_name = None

    @utils.log_steps
    def remove_packages(self):
        """Remove Packages
        """
        manager.CentosManager.remove_packages(self.conf.get('packages'))

    @utils.log_steps
    def clean_up(self):
        """Clean Up Resources
        """
        if self.conf.get('clean_up_dir'):
            utils.rm_path(self.conf.get('clean_up_dir'))
        database = self.conf.get('database')
        if database:
            if isinstance(database, collections.Sequence):
                database_list = [db['dbname'] for db in database]
            else:
                database_list = [database['dbname']]
            for db in database_list:
                LOG.debug('drop database %s', db)
                utils.run_cmd(
                    ['mysql', '-uroot',
                     '-e', '"DROP DATABASE IF EXISTS {0}"'.format(db)]
                )

    @utils.log_steps
    def stop_services(self):
        """Stop Services
        """
        for service in self.conf.get('service_names'):
            status, _ = utils.systemctl('stop', service)

    def verify(self):
        LOG.warning('Nothing to verify')

    @utils.log_steps
    def install_packages(self):
        """Install Packages"""
        utils.yum_install(self.conf.get('packages'),
                          download_dir=self.SERVICE_NAME)

    @utils.log_steps
    def start_services(self):
        """Start Services
        """
        service_names = self.conf.get('service_names')
        for service in service_names:
            status, _ = utils.systemctl('status', service)
            if status == 0:
                continue
            utils.systemctl('enable', service)
            status, _ = utils.systemctl('start', service)
            if status != 0:
                raise Exception('start {0} failed'.format(service))

    @utils.log_steps
    def after_start(self):
        """After Start Services
        """
        LOG.warning('nothing to do')

    def install(self):
        with tqdm(total=100) as process_bar:
            self.install_packages()
            process_bar.update(30)
            self.update_config_files()
            process_bar.update(30)
            self.start_services()
            process_bar.update(30)

            self.after_start()
            process_bar.update(10)

    def uninstall(self):
        with tqdm(total=100) as process_bar:
            self.stop_services()
            process_bar.update(30)

            self.remove_packages()
            process_bar.update(40)

            self.clean_up()
            process_bar.update(30)

    def update_config_files(self):
        LOG.warning('config files, nothing to do')


class OpenstackComponentInstaller(BaseCentosInstaller):

    def __init__(self):
        super().__init__()
        self.auth_services = []
        self.auth_endpoints = {}
        self.auth_client = client.Client(session=session)
        self.admin_auth = self.installer_conf.get('admin_auth')
        self.keystone_authtoken = self.installer_conf.get('keystone_authtoken')
        self.admin_client = self.make_admin_keystone_client()

    def update_config_files(self):
        """Update Config Files
        """
        conf_files = self.conf.get('conf_files')
        for conf_file in conf_files:
            file_path = conf_file.get('file')
            for group, options in conf_file.get('configs').items():
                utils.openstack_config(file_path, group, options)

    def uninstall(self):
        with tqdm(total=100) as process_bar:
            self.stop_services()
            process_bar.update(10)

            try:
                status, stdout = utils.run_openstack_cmd(
                    self.admin_openrc, ['service', 'list', '-f', 'json'])
                for service in json.loads(stdout):
                    if service.get('Name') not in self.conf.get('endpoints'):
                        continue
                    LOG.info('delete service %s', service.get('ID'))
                    utils.run_openstack_cmd(
                        self.admin_openrc,
                        ['service', 'delete', service.get('ID')])
            except json.decoder.JSONDecodeError as e:
                pass
            finally:
                process_bar.update(20)
            try:
                status, stdout = utils.run_openstack_cmd(
                    self.admin_openrc, ['endpoint', 'list', '-f', 'json'])
                for endpoint in json.loads(stdout):
                    if endpoint.get("Service Name") not in \
                            self.conf.get('endpoints'):
                        continue
                    LOG.info('delete endpoint %s', endpoint.get('ID'))
                    utils.run_openstack_cmd(
                        self.admin_openrc,
                        ['endpoint', 'delete', endpoint.get('ID')]
                    )
            except json.decoder.JSONDecodeError as e:
                process_bar.update(30)

            self.remove_packages()
            process_bar.update(30)

            self.clean_up()
            process_bar.update(10)

    def install(self):
        with tqdm(total=100) as process_bar:
            self.install_packages()
            process_bar.update(20)

            self.update_config_files()
            process_bar.update(10)

            self.init_databases()
            process_bar.update(10)

            self.db_sync()
            process_bar.update(10)

            self.start_services()
            process_bar.update(10)

            self.create_services()
            process_bar.update(10)

            self.create_auth_users()
            process_bar.update(10)

            self.after_start()
            process_bar.update(10)

    def make_admin_keystone_client(self):
        return keystone.KeystoneV3(
            auth_url=self.keystone_authtoken.get('auth_url'),
            username=self.admin_auth.get('username'),
            password=self.admin_auth.get('password'),
            project_name=self.admin_auth.get('project_name'),
            user_domain_name=self.admin_auth.get('user_domain_name'),
            project_domain_name=self.admin_auth.get('project_domain_name'))

    def create_service(self, service_type, name, description=''):
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc, ['service', 'show', name])
        if status == 0:
            LOG.warning('service %s already exists', name)
            return
        LOG.info('create service %s', name)
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc,
            ['service', 'create', '--name', name,
             '--description', '"{0}"'.format(description), service_type
             ])
        if status != 0:
            raise Exception(
                'create service {0} failed, {1}'.format(name, stdout))

    def create_endpoint(self, service, interface, url):
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc,
            ['endpoint', 'list', '--service', service,
             '--interface', interface
             ])
        if status == 0 and stdout:
            LOG.warning('endpoint (%s %s) exists', service,  interface)
            return

        LOG.info('create endpoint: %s %s', service, interface)
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc,
            ['endpoint', 'create', '--region', 'RegionOne',
             service, interface, '\'{0}\''.format(url)
             ])
        if status != 0:
            raise Exception('create endpoint failed, {0}', stdout)

    @utils.log_steps
    def create_services(self):
        """Create Services And Endpoints
        """
        service_type = self.conf.get('type')
        description = self.conf.get('description')

        for service, endpoints in self.conf.get('endpoints').items():
            LOG.debug('create service %s', service)
            self.create_service(service_type, service,
                                description=description)
            for interface, url in endpoints.items():
                LOG.debug('create endpoint %s %s', interface, url)
                self.create_endpoint(service, interface, url)

    @utils.log_steps
    def create_auth_users(self):
        """Create Auth Users
        """
        auth_users = self.conf.get('auth', [])
        if isinstance(auth_users, collections.Sequence):
            for user in auth_users:
                self.create_auth_user(user)
        else:
            self.create_auth_user(auth_users)

    def create_auth_user(self, user):
        LOG.debug('create user %s', user.get('username'))
        return self.admin_client.get_or_create_user(
            user.get('username'), user.get('domain', 'default'),
            user.get('project_name'),
            role_name=user.get('role', 'admin'),
            password=user.get('password')
        )

    def init_database(self, database):
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(
                "CREATE DATABASE IF NOT EXISTS {0};".format(
                    database.get('dbname')),
            )
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('create database failed')

        file_context = [
            "GRANT ALL ON {0}.* TO '{1}'@'%' identified by "
            "'{2}';\n".format(database.get('dbname'),
                              database.get('username'),
                              database.get('password')),
            "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'localhost' "
            "IDENTIFIED BY '{2}';\n".format(database.get('dbname'),
                                            database.get('username'),
                                            database.get('password')),
            "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'%' IDENTIFIED BY "
            "'{2}';\n".format(database.get('dbname'),
                              database.get('username'),
                              database.get('password')),

            "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'{3}' IDENTIFIED BY "
            "'{2}';\n".format(database.get('dbname'),
                              database.get('username'),
                              database.get('password'),
                              socket.gethostname()),
        ]
        LOG.debug('db file:\n %s', ''.join(file_context))
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.writelines(file_context)
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('set privileges failed ')

    @utils.log_steps
    def init_databases(self):
        """Init databases
        """
        databases = self.conf.get('database', [])
        if isinstance(databases, collections.Sequence):
            for database in databases:
                self.init_database(database)
        else:
            self.init_database(databases)

    @utils.log_steps
    def db_sync(self):
        """Update Database
        """
        status, _ = utils.run_cmd(self.conf.get('db_sync_cmd'))
        if status != 0:
            raise Exception('db sync failed')
