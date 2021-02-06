import  os
import sys

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

from agents import service_status  # noqa
from common import log

LOG = log.LOG


def main():
    service_agent = service_status.ServiceStatusAgent()
    service_agent.start()
    LOG.info('start cloud-agent ...')


if __name__ == '__main__':
    main()
