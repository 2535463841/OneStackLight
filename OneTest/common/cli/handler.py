import logging
import prettytable

from common import manager
from common.db import models
# from common import logger
from lib import utils

LOG = logging.getLogger(__name__)


class Tasks(object):
    MODEL = models.Tasks

    @classmethod
    def _list_with_cmd(cls, args):
        pt = prettytable.PrettyTable()
        pt.field_names = ["id", "project", "cmd", "status", "result", 'start', 'end', 'output']
        for task in cls.MODEL.select():
            try:
                case = task.case.name if args.detail else task.case_id
            except:
                LOG.error("case %s not found", case)
                case = "NotFound"
            try:
                project = task.project.name if args.detail else task.project.id
            except:
                LOG.error("project %s not found", project)
                project = "NotFound"

            if args.project and args.project not in task.project.name:
                continue
            if args.name and case and args.name in case:
                continue

            try:
                cmd = "{0} {1}".format(task.case.cmd, task.options)
            except:
                cmd = ""

            pt.add_row([
                task.id, project, cmd, task.status,
                task.result,
                utils.format_timestamp(task.start),
                utils.format_timestamp(task.end),
                task.output])
        return pt

    @classmethod
    def _list(cls, args):
        pt = prettytable.PrettyTable()
        pt.field_names = ["id", "project", "case", 'options', "status", "result", "start", "end"]
        for task in cls.MODEL.select():
            try:
                case = task.case.name if args.detail else task.case_id
            except:
                LOG.error("case %s not found", task.case_id)
                case = task.case_id

            try:
                project = task.project.name if args.detail else task.project.id
            except:
                LOG.error("project %s not found", project)
                project = "NotFound"
            if args.project and args.project not in task.project.name:
                continue
            if args.name and case and args.name not in case:
                continue
            pt.add_row([task.id, project, case, task.options, task.status, task.result,
                        utils.format_timestamp(task.start),
                        utils.format_timestamp(task.end)
                        ])
        return pt

    @classmethod
    def list(cls, args):
        if args.cmd:
            pt = cls._list_with_cmd(args)
        else:
            pt = cls._list(args)
        print(pt)

    @classmethod
    def create(cls, args):
        LOG.info('create Task: options=%s', args.options)
        project = args.project or "default"
        project_select = TestProject.get_by_name_or_id(project)
        if project_select.count() == 0:
            LOG.error('project %s not found', project)
            return
        LOG.debug('project %s', project)
        LOG.debug('case: %s', models.TestCases.get_by_id(int(args.case)))
        models.Tasks.create(
            project=project_select[0],
            case=models.TestCases.get_by_id(int(args.case)),
            options=args.options,
            status='waiting'
        )
        print('create {0} success'.format(cls.MODEL))

    @classmethod
    def delete(cls, args):
        changed_row = cls.MODEL.delete_by_id(args.id)
        if changed_row == 0:
            print('test project with id {0} not found'.format(args.id))
        else:
            print('delete test project {0} success'.format(args.id))

    @classmethod
    def get_by_id_or_name(cls, id_or_name):
        select = cls.MODEL.filter(id=id_or_name).select()
        if select.count() == 0:
            select = models.TestProject.filter(name=id_or_name).select()
        return select

    @classmethod
    def update(cls, args):
        select = cls.get_by_id_or_name(args.id)
        if select.count() == 0:
            LOG.error('task %s not found', args.id)
            return
        update_params = {}
        if args.status:
            update_params['status'] = args.status
        if args.options:
            update_params['options'] = args.options

        if not update_params:
            LOG.error("update params is null")
            return
        manager.Tasks.update(select[0].id, **update_params)
        LOG.info('update task %s success', select[0].id)


class TestCases(object):
    MODEL = models.TestCases

    @classmethod
    def list(cls, args):
        print('list {0}'.format(cls.__name__))
        pt = prettytable.PrettyTable()
        pt.field_names = ["id", "name", "cmd", 'description']
        list_filter = {}
        if args.name:
            list_filter['name'] = args.name
        for case in manager.TestCases.list(**list_filter):
            pt.add_row([case.id, case.name, case.cmd, case.description])
        print(pt)

    @classmethod
    def create(cls, args):
        cls.MODEL.create(name=args.name, cmd=args.cmd, description=args.description)
        print('create test project success')

    @classmethod
    def delete(cls, args):
        changed_row = cls.MODEL.delete_by_id(args.id)
        if changed_row == 0:
            print('test case with id {0} not found'.format(args.id))
        else:
            print('delete test case {0} success'.format(args.id))


class TestProject(object):

    @classmethod
    def get_by_name_or_id(cls, id_or_name):
        project_select = models.TestProject.filter(id=id_or_name).select()
        if project_select.count() == 0:
            project_select = models.TestProject.filter(name=id_or_name).select()
        return project_select

    @staticmethod
    def list(args):
        pt = prettytable.PrettyTable()
        pt.field_names = ["id", "name"]
        for project in models.TestProject().select():
            if not args.name or (args.name and args.name in project.name):
                pt.add_row([project.id, project.name])
        print(pt)

    @staticmethod
    def create(args):
        project_select = models.TestProject.filter(name=args.name).select()
        if project_select.count() > 0:
            print('ERROR: create test project with name {0} exists'.format(args.name))
            return
        models.TestProject.create(name=args.name)
        print('create test project success'.format(args.name))

    @staticmethod
    def delete(args):
        changed_row = models.TestProject.delete_by_id(args.id)
        if changed_row == 0:
            print('test project with id {0} not found'.format(args.id))
        else:
            print('delete test project {0} success'.format(args.id))
