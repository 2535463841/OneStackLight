import os
import sys

import logging.config

from simplelib.common import subcmd

sys.path.append(
    os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
)

from common.hosts import model                      # noqa
from common import config                           # noqa


CONF = config.CONF
logging.config.fileConfig(CONF.log.logging_config)

LOG = logging.getLogger(__name__)


class HostManager(object):

    @staticmethod
    def add_host(args):
        model.Hosts.create_table()
        host = model.Hosts.get_or_none(host=args.host, group=args.group)
        if host:
            LOG.error('host already exists.')
            return
        model.Hosts.create(host=args.host,
                           user=args.user,
                           password=args.password or '',
                           group=args.group
                           )
        LOG.error('host added success')

    @staticmethod
    def delete_host(args):
        model.Hosts.create_table()
        host = model.Hosts.get_or_none(host=args.host, group=args.group)
        if not host:
            LOG.error('host not exists.')
            return
        model.Hosts.delete_by_id(host.id)
        LOG.error('host added success')


def main():
    parser = subcmd.SubCommandsParser()
    parser.register_sub_command(
        'host-add', 'add hosts',
        [('host', dict(help='ip/name for host')),
         ('-g', '--group', dict(required=True, help='user name')),
         ('-u', '--user', dict(required=True, help='user name')),
         ('-p', '--password', dict(help='ip/name for host')),
         ('-i', '--identity_file', dict(help='ip/name for host')),
         ],
        func='add_host'
    )

    parser.register_sub_command(
        'host-delete', 'add hosts',
        [('host', dict(help='ip/name for host')),
         ('-g', '--group', dict(required=True, help='user name')),
         ],
        func='delete_host'
    )
    args = parser.parse_args(sys.argv[1:])
    func = getattr(HostManager, args.func)
    func.__call__(args)


if __name__ == '__main__':
    main()
