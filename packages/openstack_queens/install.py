#!/user/bin/python3

import argparse
import logging
import sys
import re
import os
import platform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # noqa


from common import log
from common import manager
import importlib
import glob

LOG = log.LOG


def main():
    for f in glob.glob('installer/*.py', ):
        importlib.import_module(f.replace('.py', '').replace('/', '.'))
    parser = argparse.ArgumentParser()
    parser.add_argument('service',
                        choices=manager.SERVICE_SUPPORTED.keys(),
                        help='service to install')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='show debug message')

    parser.add_argument('-u', '--uninstall', action='store_true',
                        help='uninstall')

    args = parser.parse_args()
    if args.debug:
        LOG.setLevel(logging.DEBUG)
    LOG.debug(args)
    LOG.info('*************************************************************')
    LOG.info("*       System: %s %s", platform.system(), platform.release())
    LOG.info("*      Release: %s", platform.platform().split('-with-')[-1])
    LOG.info("* Architecture: %s", platform.architecture()[0])
    LOG.info('*************************************************************')

    if re.search("centos", platform.platform(), re.IGNORECASE):
        installer = manager.SERVICE_SUPPORTED[args.service]()
    else:
        LOG.error("platform is not supported")
        sys.exit(1)

    if args.uninstall:
        LOG.info(
            "========== Uninstall {0:>8} ==========".format(args.service))
        installer.uninstall()
    else:
        LOG.info("=========== Install {0:>8} ===========".format(
            args.service))
        installer.install()
        LOG.info("=============== Verify =================")
        installer.verify()


if __name__ == '__main__':
    main()
