import os

from simplelib.common import config

CONF = config.ConfigOpts()


def register_configuration():
    server_opts = [
        config.IntOption('port', default=80),
        config.BooleanOption('app_debug', default=False),
        config.Option('file_upload_path', default='./file_upload_path'),
        config.Option('home_page', default='/views/home.html'),
        config.BooleanOption('install_agent', default=True),
        config.Option('agent_path', default='/opt'),
        config.Option('home', default=None)
    ]

    sqlite_opts = [
        config.Option('connection', default=os.path.join('data', 'sqlite.db')),
    ]
    log_opts = [
        config.Option('debug', default=False),
        config.Option('logging_config',
                      default=os.path.join('conf', 'logging.conf')),
    ]

    collector_opt = [
        config.IntOption('nn_rpc_activity_port', default=9000),
        config.IntOption('nn_rpc_detail_activity_port', default=9000),
        config.IntOption('rm_rpc_activity_port', default=8031),
        config.IntOption('rm_rpc_detail_activity_port', default=8031),

        config.IntOption('jmx_timeout', default=60),
        config.IntOption('jmx_retry_times', default=5),
        config.IntOption('jmx_retry_interval', default=2),
    ]
    CONF.register_opts(sqlite_opts, group='sqlite')
    CONF.register_opts(server_opts, group='server')
    CONF.register_opts(log_opts, group='log')
    CONF.register_opts(collector_opt, group='collector')


# register default config
register_configuration()

# load config from config file
# conf_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
#                          constants.DEFAULT_CONF_FILE)

# CONF.load_configuration(conf_file)
