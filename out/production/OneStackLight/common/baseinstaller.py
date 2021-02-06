import os
import abc
import socket
from tqdm import tqdm

from common import utils
from common import log

LOG = log.LOG


class BaseCentosInstaller:
    PACKAGES = []
    SERVICES = []

    def __init__(self):
        self.host = socket.gethostname()
        self.admin_openrc = os.path.join(os.path.expanduser('~'),
                                         'admin_openrc')

    @utils.log_steps
    def remove_packages(self):
        """Remove Packages
        """
        LOG.info('remove packages %s', self.PACKAGES)
        utils.yum_remove(self.SERVICES)

    @abc.abstractmethod
    @utils.log_steps
    def clean_up(self):
        """Clean Up Resources
        """
        pass

    @utils.log_steps
    def stop_services(self):
        """Stop Services
        """
        for service in self.SERVICES:
            LOG.info('stopping service %s', service)
            status, _ = utils.systemctl('stop', service)

    def install(self):
        with tqdm(total=100) as process_bar:
            self.install_packages()
            process_bar.update(20)

            self.create_authorization()
            process_bar.update(20)

            self.init_database()
            process_bar.update(10)

            self.update_config_files()
            process_bar.update(10)

            self.update_database()
            process_bar.update(20)

            self.start_services()
            process_bar.update(10)

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

    def verify(self):
        LOG.warning('Nothing to verify')

    @utils.log_steps
    def install_packages(self):
        """Install Packages"""
        utils.yum_install(self.packages)

    @abc.abstractmethod
    def update_config_files(self):
        """Update Config Files
        """
        pass

    @utils.log_steps
    def start_services(self):
        """Start Services
        """
        for service in self.SERVICES:
            status, _ = utils.systemctl('status', service)
            if status == 0:
                continue
            utils.systemctl('enable', service)
            status, _ = utils.systemctl('start', service)
            if status != 0:
                raise Exception('start {0} failed'.format(service))

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
    def after_start(self):
        """After Start Services
        """
        LOG.warning('nothing to do')

    @abc.abstractmethod
    def create_authorization(self):
        pass

    @abc.abstractmethod
    def init_database(self):
        pass

    @abc.abstractmethod
    def update_database(self):
        pass

