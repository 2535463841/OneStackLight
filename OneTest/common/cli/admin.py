import os
import sys

if os.getcwd() not in sys.path:  # noqa
    sys.path.append(os.getcwd())  # noqa

from simplelib.common import subcmd
from common.cli import handler


def main():
    sub_parser = subcmd.SubCommandsParser()
    sub_parser.register_sub_command(
        "project-list", "list test project",
        [("-n", "--name", dict(help="the name of test project"))],
        func=handler.TestProject.list,
    )
    sub_parser.register_sub_command(
        "project-create", "create test project",
        [("name", dict(help="the name of test project"))],
        func=handler.TestProject.create,
    )
    sub_parser.register_sub_command(
        "project-delete", "create test project",
        [("id", dict(help="the id of test project"))],
        func=handler.TestProject.delete,
    )
    sub_parser.register_sub_command(
        "task-list", "list test project",
        [
            ("-n", "--name", dict(help="the name of test project")),
            ("-p", "--project", dict(help="the name of test project")),
            ("--detail", dict(help="the name of test project", action='store_true')),
            ("--cmd", dict(help="the name of test project", action='store_true'))
        ],
        func=handler.Tasks.list,
    )
    sub_parser.register_sub_command(
        "task-create", "create test project",
        [
            ("case", dict(help="the id name of case", )),
            ("-o", "--options", dict(help="the name of test project", default='')),
            ("-p", "--project", dict(help="the name of test project", )),
        ]
        ,
        func=handler.Tasks.create,
    )
    sub_parser.register_sub_command(
        "task-delete", "create test project",
        [("id", dict(help="the id of test project"))],
        func=handler.Tasks.delete,
    )
    sub_parser.register_sub_command(
        "task-update", "create test project",
        [
            ("id", dict(help="the id of test project")),
            ("-s", "--status", dict(help="the status of task")),
            ("-o", "--options", dict(help="the options of task")),
         ],
        func=handler.Tasks.update,
    )

    sub_parser.register_sub_command(
        "testcase-list", "list test project",
        [("-n", "--name", dict(help="the name of test project"))],
        func=handler.TestCases.list,
    )
    sub_parser.register_sub_command(
        "testcase-create", "create test project",
        [("name", dict(help="the name of test project")),
         ("-c", "--cmd", dict(help="the name of test project", default='')),
         ("--description", dict(help="the name of test project", default=''))
         ],
        func=handler.TestCases.create,
    )
    sub_parser.register_sub_command(
        "testcase-delete", "create test project",
        [("id", dict(help="the id of test project"))],
        func=handler.TestCases.delete,
    )

    args = sub_parser.parse_args()
    if not hasattr(args, 'func'):
        sub_parser.parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == '__main__':
    main()



import os
