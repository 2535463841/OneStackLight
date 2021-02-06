import os
import socket
import tempfile
import json
import yaml
import collections

from tqdm import tqdm

from common import utils
from common import log

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


class OpenstackInstallMixin(object):

    def __init__(self):
        self.conf = None
        self.admin_openrc = None
        self.auth_services = []
        self.auth_endpoints = {}

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
        auth_users = self.conf.get('auth')
        if isinstance(auth_users, collections.Sequence):
            for user in auth_users:
                self.create_auth_user(user)
        else:
            self.create_auth_user(auth_users)

    def _role_exists(self, role_name):
        status, _ = utils.run_openstack_cmd(
            self.admin_openrc, ['role', 'show', role_name]
        )
        return status == 0

    def _domain_exists(self, domain):
        status, _ = utils.run_openstack_cmd(
            self.admin_openrc, ['domain', 'show', domain]
        )
        return status == 0

    def create_role(self, role):
        if not self._role_exists(role):
            utils.run_openstack_cmd(
                self.admin_openrc, ['role', 'create', role]
            )

    def create_domain(self, domain):
        if not self._domain_exists(domain):
            description = '"{0} Domain"'.format(domain.capitalize())
            utils.run_openstack_cmd(
                self.admin_openrc,
                ['domain', 'create', domain, '--description', description]
            )

    def create_auth_user(self, user):
        project_create_cmd = [
            'project', 'create', user.get('project_name'),
            '--description', '"{0}"'.format(user.get('description', ''))
        ]
        if user.get('role'):
            self.create_role(user.get('role'))
        if user.get('domain'):
            self.create_domain(user.get('domain'))
            project_create_cmd.extend(['--domain', user.get('domain')])

        utils.run_openstack_cmd(
            self.admin_openrc, project_create_cmd
        )
        if user.get('username'):
            user_create_cmd = [
                'user', 'create', user.get('username'),
                '--password', user.get('password')
            ]
            if user.get('domain'):
                user_create_cmd.extend(['--domain', user.get('domain')])
            utils.run_openstack_cmd(self.admin_openrc, user_create_cmd)

        if user.get('role'):
            utils.run_openstack_cmd(
                self.admin_openrc,
                ['role', 'add', user.get('role'),
                 '--user', user.get('username'),
                 '--project', user.get('project_name')])

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
        databases = self.conf.get('database')
        if isinstance(databases, collections.Sequence):
            for database in databases:
                self.init_database(database)
        else:
            self.init_database(databases)

    @utils.log_steps
    def db_sync(self):
        """Update Database
        """
        status, stdout = utils.run_cmd(self.conf.get('db_sync_cmd'))
        if status != 0:
            raise Exception('db sync failed')


class BaseCentosInstaller:

    def __init__(self):
        self.host = socket.gethostname()
        self.admin_openrc = os.path.join(os.path.expanduser('~'),
                                         'admin_openrc')
        self.db_name = None
        self.conf = None

    @utils.log_steps
    def remove_packages(self):
        """Remove Packages
        """
        utils.yum_remove(self.conf.get('packages'))

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
                          download_dir=self.conf.get('type'))

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


class OpenstackComponentInstaller(BaseCentosInstaller,
                                  OpenstackInstallMixin):

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

            self.stop_services()
            process_bar.update(10)

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
