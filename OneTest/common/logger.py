import logging
import logging.config

from common import config

CONF = config.CONF


def config_log(config_file):
    logging.config.fileConfig(config_file)


config_log(CONF.log.logging_config)

LOG = logging.getLogger('root')
