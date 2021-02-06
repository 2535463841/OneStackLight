
import logging
from logging import handlers

import config

# FORMAT = '%(asctime)s %(levelno)s %(filename)s:%(lineno)s %(message)s'
FORMAT = '%(levelname)s %(message)s'

logging.basicConfig(level=logging.INFO, format=FORMAT)

file_handler = handlers.RotatingFileHandler(config.LOG_FILE)
# file_handler.setFormatter(FORMAT)
file_handler.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

LOG = logging.RootLogger(logging.DEBUG if config.DEBUG else logging.INFO)
LOG.addHandler(file_handler)
