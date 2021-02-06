from oslo_config import cfg


keystone_opts = [
    cfg.StrOpt('admin_password', default='admin1234'),
    cfg.StrOpt('dbname', default='keystone'),
    cfg.StrOpt('keystone_db_user', default='keystone'),
    cfg.StrOpt('keystone_db_password', default='admin1234'),
    cfg.StrOpt('keystoneadmin_db_user', default='keystoneadmin'),
    cfg.StrOpt('keystoneadmin_db_password', default='admin1234'),
]
neutron_opts = [
    cfg.StrOpt('admin_password', default='admin1234'),
    cfg.StrOpt('dbname', default='keystone'),
    cfg.StrOpt('neutron_db_user', default='neutron'),
    cfg.StrOpt('neutron_db_password', default='admin1234'),
]

amqp_opts = [
    cfg.StrOpt('host', default='controller'),
    cfg.StrOpt('openstack_user', default='openstack'),
    cfg.StrOpt('openstack_pass', default='openstack1234'),
    cfg.BoolOpt('enable_management', default=True),
]

cinder_opts = [
    cfg.StrOpt('host', default='controller'),
    cfg.StrOpt('dbname', default='cinder'),
    cfg.StrOpt('cinder_db_user', default='cinder'),
    cfg.StrOpt('cinder_db_pass', default='cinder1234'),
    cfg.StrOpt('admin_password', default='cinder1234'),
]

glance_opts = [
    cfg.StrOpt('host', default='controller'),
    cfg.StrOpt('dbname', default='glance'),
    cfg.StrOpt('glance_db_user', default='glance'),
    cfg.StrOpt('glance_db_pass', default='glance1234'),
    cfg.StrOpt('admin_password', default='glance1234'),
]

CONF = cfg.CONF
CONF.register_opts(keystone_opts, group='keystone')
CONF.register_opts(neutron_opts, group='neutron')
CONF.register_opts(amqp_opts, group='amqp')
CONF.register_opts(cinder_opts, group='cinder')
CONF.register_opts(glance_opts, group='glance')
