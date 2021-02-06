import os
import tempfile
import json

from common import config
from common import log
from common import utils
from common import baseinstaller
from common import manager

CONF = config.CONF
LOG = log.LOG


@manager.register_service('neutron')
class NeutronCentosInstaller(baseinstaller.BaseCentosInstaller):

    def create_authorization(self):
        pass

    def init_database(self):
        pass

    def update_database(self):
        pass

    @utils.log_steps
    def update_config_files(self):
        """Config Sservices
        """
        self.create_neutron_user()
        self.config_neutron()
        self.set_neutron_database()
        self.neutron_db_upgrade()
        self.create_neutron_endpoint()

    @utils.log_steps
    def clean_up(self):
        """Cleanup Resources
        """
        admin_openrc = os.path.join(os.path.expanduser('~'), 'admin_openrc')
        LOG.info('deleting neutron service')
        utils.run_openstack_cmd(
            admin_openrc, ['service', 'delete', 'neutron'])

        LOG.info('deleting neutron endpoint')
        status, stdout = utils.run_openstack_cmd(
            admin_openrc, ['endpoint', 'list', '-f', 'json'])

        for endpoint in json.loads(stdout):
            if endpoint.get("Service Name") != "neutron":
                continue
            utils.run_openstack_cmd(
                admin_openrc, ['endpoint', 'delete', endpoint.get('ID')]
            )
        utils.rm_path(self.cleanup_resources)

    def __init__(self):
        super().__init__(
            ['openstack-neutron', 'openstack-neutron-ml2',
             'openstack-neutron-linuxbridge', 'etables'],
            ['neutron-server'])

        self.neutron_conf = "/etc/neutron/neutron.conf"
        self.ml2_conf = "/etc/neutron/plugins/ml2/ml2_conf.ini"
        self.bridge_conf = '/etc/neutron/plugins/ml2/linuxbridge_agent.ini'
        self.dhcp_conf = '/etc/neutron/dhcp_agent.ini'
        self.metadata_conf = '/etc/neutron/metadata_agent.ini'

        self.cleanup_resources = [
            "/var/lib/mysql",
            "/etc/httpd/conf.d/wsgi-keystone.conf",
            "/var/log/keystone"
        ]

        self.dbname = CONF.neutron.dbname
        self.user = CONF.neutron.neutron_db_user
        self.password = CONF.neutron.neutron_db_password
        self.admin_password = CONF.neutron.admin_password

        self.endpoints = [
            ('public', 'http://{0}:9696'.format(self.host)),
            ('internal', 'http://{0}:9696'.format(self.host)),
            ('admin', 'http://{0}:9696'.format(self.host))
        ]
        self.admin_openrc = os.path.join(os.path.expanduser('~'),
                                         'admin_openrc')

    @utils.log_steps
    def set_neutron_database(self):
        """Create neutron Database
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

                "GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'{3}' IDENTIFIED BY "
                "'{2}';\n".format(self.dbname, self.user,
                                  self.password, self.host),
            ])
            f.flush()
            status, stdout = utils.run_cmd(['mysql', '-uroot', '<', f.name])
            if status != 0:
                raise Exception('set privileges failed ')

    @utils.log_steps
    def config_neutron(self):
        """Config Neutron
        """
        configs = {
            'database': {
                'connection': 'mysql://{0}:{1}@{2}/{3}'.format(
                    self.user, self.password, self.host, self.dbname)
            },
            'DEFAULT': {
                'core_plugin': 'ml2',
                'service_plugins': '',
                'transport_url': 'rabbit://openstack:openstack@{0}'.format(
                    self.host),
                'auth_strategy': 'keystone',
                'notify_nova_on_port_status_changes': True,
                'notify_nova_on_port_data_changes': True
            },
            'keystone_authtoken':{
                'www_authenticate_uri': "http://{0}:5000".format(self.host),
                'auth_url': "http://{0}:5000".format(self.host),
                'memcached_servers': '{0}:11211'.format(self.host),
                'auth_type': 'password',
                'project_domain_name': 'default',
                'user_domain_name': 'default',
                'project_name': 'service',
                'username': 'neuron',
                'password': self.admin_password,
            },
            'nova': {
                'auth_url': "http://{0}:5000".format(self.host),
                'auth_type': 'password',
                'project_domain_name': 'default',
                'user_domain_name': 'default',
                'region_name': 'RegionOne',
                'project_name': 'service',
                'username': 'nova',
                'password': self.admin_password,
            },
            'oslo_concurrency': {
                'lock_path': '/var/lib/neutron/tmp'
            }
        }
        ml2_configs = {
            'ml2': {
                'type_drivers': 'flat,vlan',
                'tenant_network_types': '',
                'mechanism_drivers': 'linuxbridge',
                'extension_drivers': 'port_security',
            },
            'ml2_type_flat': {
                'flat_networks': 'provider'
            }
        }
        bridge_configs = {
            'linux_bridge': {
                'physical_interface_mappings':  'provider:eth1',
            },
            'vxlan': {
                'enable_vxlan': False,
            },
            'securitygroup': {
                'enable_security_group': True,
                'firewall_driver': 'neutron.agent.linux.iptables_firewall.IptablesFirewallDriver'
            }
        }
        metadata_configs = {
            'DEFAULT': {
                'interface_driver': 'linuxbridge',
                'metadata_proxy_shared_secret': 'neutron',
            }
        }
        dhcp_configs = {
            'DEFAULT': {
                'nova_metadata_host': self.host,
                'dhcp_driver': 'neutron.agent.linux.dhcp.Dnsmasq',
                'enable_isolated_metadata': True
            }
        }
        for section, opts in configs.items():
            for opt, value in opts.items():
                utils.openstack_config_set(self.neutron_conf,
                                           section, opt, value)
        for section, opts in ml2_configs.items():
            for opt, value in opts.items():
                utils.openstack_config_set(self.ml2_conf, section, opt, value)
        for section, opts in bridge_configs.items():
            for opt, value in opts.items():
                utils.openstack_config_set(self.bridge_conf,
                                           section, opt, value)
        for section, opts in dhcp_configs.items():
            for opt, value in opts.items():
                utils.openstack_config_set(self.dhcp_conf,
                                           section, opt, value)
        for section, opts in metadata_configs.items():
            for opt, value in opts.items():
                utils.openstack_config_set(self.metadata_conf,
                                           section, opt, value)

        if not os.path.exists('/etc/neutron/plugin.ini'):
            utils.run_cmd([
                'ln', '-s', self.ml2_conf, '/etc/neutron/plugin.ini'
            ])

    @utils.log_steps
    def neutron_db_upgrade(self):
        """Update Neutron DB
        """
        utils.run_cmd([
            'neutron-db-manage', '--config-file', self.neutron_conf,
            '--config-file', self.ml2_conf,
            'upgrade', 'head'
        ])

    @utils.log_steps
    def create_neutron_user(self):
        """Create Neutron User
        """
        utils.run_openstack_cmd(
            self.admin_openrc,
            ['user', 'create', '--domain', 'default',
             '--password', self.admin_password, 'neutron'])

    @utils.log_steps
    def create_neutron_endpoint(self):
        """Create Neutron Endpoint
        """
        LOG.info('create network service')
        admin_openrc = os.path.join(os.path.expanduser('~'), 'admin_openrc')
        status, stdout = utils.run_cmd([
            'source', admin_openrc, '&&',
            'openstack', 'service', 'show', 'network'
        ])
        if status != 0:
            status, stdout = utils.run_cmd([
                'source', admin_openrc, '&&',
                'openstack', 'service', 'create', '--name', 'neutron',
                '--description', '"OpenStack Networking"', 'network'
            ])
            if status != 0:
                raise Exception(
                    'create neutron service failed, {0}'.format(stdout))
        else:
            LOG.warning('service network exists')
        for interface, url in self.endpoints:
            status, stdout = utils.run_cmd([
                'source', admin_openrc, '&&',
                'openstack', 'endpoint', 'list', '--service', 'neutron',
                '--interface', interface
            ])
            if status == 0 and stdout:
                continue
            LOG.info('create endpoint: %s %s', interface, url)
            status, stdout = utils.run_cmd([
                'source', admin_openrc, '&&',
                'openstack', 'endpoint', 'create', '--region', 'RegionOne',
                'network', interface, url
            ])
            if status != 0:
                raise Exception(
                    'create neutron endpoint failed, {0}'.format(stdout))
