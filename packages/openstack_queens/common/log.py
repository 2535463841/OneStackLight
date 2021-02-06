import sys
import logging


LOG = logging.RootLogger(logging.INFO)
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s: %(message)s",
                      '%Y-%m-%d %H:%M:%S')
)
LOG.addHandler(stream_handler)
