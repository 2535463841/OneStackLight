import os
from os import path
from os.path import dirname, join
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
from common.lib import executor


LOG = log.LOG


class BaseCentosServiceDriver:
    def __init__(self, service_name, services_conf):
        self.service_name = service_name
        self.services_conf = services_conf
        self.admin_openrc = os.path.join(os.path.expanduser('~'),
                                         'admin_openrc')
        self.conf = self.services_conf.get(self.service_name)
        if not self.conf:
            raise Exception('conf of {0} is None'.format(self.service_name))
        self.manager = manager.CentosManager()
        self.db_name = None
        self.executor = executor.CentosExecutor()

        self.install_steps = [
            self.install_packages,
            self.update_config_files,
            self.before_start_services,
            self.start_services,
            self.after_start_services,
        ]
        self.uninstall_steps = [
            self.stop_services,
            self.remove_packages,
            self.clean_up,
        ]

    def remove_packages(self):
        """Remove Packages
        """
        self.executor.yum.execute(['remove', '-y'] + self.conf.get('packages'))

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

    def stop_services(self):
        """Stop Services"""
        for service in self.conf.get('service_names'):
            status, _ = utils.systemctl('stop', service)

    def verify(self):
        LOG.warning('Nothing to verify')

    def install_packages(self):
        """Install packages"""
        packages = self.conf.get('packages')
        status, _, _ = self.executor.rpm.execute(['-q'] + packages)

        if status == 0:
            LOG.debug('packages have been installed')
            return
        LOG.debug('download packages %s', packages)

        download_dir = os.path.join('rpm_packages', self.service_name)

        status, stdout, _ = self.executor.yum.execute([
            'install', '--downloadonly',
            '--downloaddir', download_dir] + packages)
        if status != 0:
            raise Exception("download packages failed, {0}".format(stdout))
        LOG.debug('install packages %s', packages)
        status, stdout, _ = self.executor.yum.execute(
            ['install', '-y', os.path.join(download_dir, '*.rpm')]
        )
        if status != 0 and 'Error: Nothing to do' not in stdout:
            raise Exception("install packages failed")

    def start_services(self):
        """Start Services"""
        service_names = self.conf.get('service_names')
        for service in service_names:
            status, _ = utils.systemctl('status', service)
            if status == 0:
                continue
            utils.systemctl('enable', service)
            status, _ = utils.systemctl('start', service)
            if status != 0:
                raise Exception('start {0} failed'.format(service))

    def before_start_services(self):
        """Init Before Start Services
        """
        self.init_before_start_services()

    def init_before_start_services(self):
        pass

    def after_start_services(self):
        """Init After Start Services
        """
        self.init_after_start_services()

    def init_after_start_services(self):
        pass

    def install(self):
        with tqdm(total=len(self.install_steps)) as process_bar:
            for step in self.install_steps:
                process_bar.write(step.__doc__.strip())
                step()
                process_bar.update(1)

    def uninstall(self):
        with tqdm(total=len(self.uninstall_steps)) as process_bar:
            for step in self.uninstall_steps:
                process_bar.write(step.__doc__.strip())
                step()
                process_bar.update(1)

    def update_config_files(self):
        LOG.warning('config files, nothing to do')


class OpenstackSerivceDriver(BaseCentosServiceDriver):

    def __init__(self, service_name, services_conf):
        super().__init__(service_name, services_conf)
        self.auth_services = []
        self.auth_endpoints = {}
        self.auth_client = client.Client(session=session)
        self.admin_auth = self.services_conf.get('admin_auth')
        self.keystone_authtoken = self.services_conf.get('keystone_authtoken')
        self.admin_client = self.make_admin_keystone_client()
        
        self.install_steps = [
            self.install_packages,
            self.update_config_files,
            self.init_databases,
            self.before_start_services,
            self.db_sync,
            self.start_services,
            self.create_services,
            self.create_auth_users,
            self.after_start_services,
        ]
        self.uninstall_steps = self.uninstall_steps + [
            self.clean_up_service_endpoints
        ]

    def update_config_files(self):
        """Update Config Files"""
        conf_files = self.conf.get('conf_files')
        for conf_file in conf_files:
            file_path = conf_file.get('file')
            pardir = os.path.dirname(file_path)
            if not os.path.exists(pardir):
                os.makedirs(pardir)
            for group, options in conf_file.get('configs').items():
                utils.openstack_config(file_path, group, options)

    def clean_up_service_endpoints(self):
        """Clean up service and endpionts"""
        try:
            status, stdout = utils.run_openstack_cmd(
                self.admin_openrc, ['service', 'list', '-f', 'json'])
            for service in json.loads(stdout):
                if service.get('Name') not in self.conf.get('endpoints'):
                    continue
                LOG.debug('delete service %s', service.get('ID'))
                utils.run_openstack_cmd(
                    self.admin_openrc,
                    ['service', 'delete', service.get('ID')])
        except json.decoder.JSONDecodeError as e:
            pass
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
            pass

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

    def create_services(self):
        """Create Services And Endpoints"""
        service_type = self.conf.get('type')
        description = self.conf.get('description')

        for service, endpoints in self.conf.get('endpoints').items():
            LOG.debug('create service %s', service)
            self.create_service(service_type, service,
                                description=description)
            for interface, url in endpoints.items():
                LOG.debug('create endpoint %s %s', interface, url)
                self.create_endpoint(service, interface, url)

    def create_auth_users(self):
        """Create Auth Users"""
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

    def init_databases(self):
        """Init databases"""
        databases = self.conf.get('database', [])
        if isinstance(databases, collections.Sequence):
            for database in databases:
                self.init_database(database)
        else:
            self.init_database(databases)

    def db_sync(self):
        """Update Database"""
        status, stdout = utils.run_cmd(self.conf.get('db_sync_cmd'))
        if status != 0:
            raise Exception('db sync failed, {0}'.format(stdout))
