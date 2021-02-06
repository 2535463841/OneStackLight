# coding: UTF-8
import time
from playhouse.shortcuts import model_to_dict
from simplelib.common import threadpool

from common import logger
from common.db import models
from simplelib.linux import executor
LOG = logger.LOG


class BaseModelManager(object):
    MODEL = models.BaseModel

    @classmethod
    def list(cls, **kwargs):
        model_select = cls.MODEL.select()
        if kwargs:
            model_select = model_select.filter(**kwargs)
        for m in model_select:
            yield m

    @classmethod
    def create(cls, **kwargs):
        LOG.debug('create %s, kwargs=%s', cls.MODEL.__name__, kwargs)
        LOG.debug(kwargs.get("project"))
        return cls.MODEL.create(**kwargs)

    @classmethod
    def delete(cls, inst_id):
        changed_row = cls.MODEL.delete_by_id(inst_id)
        return changed_row

    @classmethod
    def get(cls, inst_id):
        return cls.MODEL.get_by_id(inst_id)

    @classmethod
    def update(cls, inst_id, **kwargs):
        model = cls.get(inst_id)
        for k, v in kwargs.items():
            setattr(model, k, v)
        model.save()
        return model


class TestCases(BaseModelManager):
    MODEL = models.TestCases


class TestProject(BaseModelManager):
    MODEL = models.TestProject


class Tasks(BaseModelManager):
    MODEL = models.Tasks


class Manager(object):
    SYNC_INTERVAL = 5

    def __init__(self):
        self.stop = False

    @staticmethod
    def list_testcase(**kwargs):
        test_cases = []
        for case in TestCases.list(**kwargs):
            test_cases.append(model_to_dict(case))
        return test_cases

    @staticmethod
    def create_testcase(name, cmd, description=None):
        return TestCases.create(name=name, cmd=cmd,
                                description=description or '')

    @staticmethod
    def list_tasks(**kwargs):
        tasks = []
        for task in Tasks.list(**kwargs):
            tasks.append(model_to_dict(task))
        return tasks

    @staticmethod
    def execute_task(task):
        LOG.debug('start to deal with Task %s' % task)
        run_cmd = "{0} {1}".format(task['case']['cmd'], task['options'])
        LOG.debug('run cmd: %s', run_cmd)
        try:
            Tasks.update(task['id'], start=time.time(), status='running')

            cmd = task['case']['cmd'] + task['options']
            linux_executor = executor.LinuxExecutor(cmd[0])
            status, stdout, stderr = linux_executor.with_options(
                cmd[1:]).execute()
            LOG.debug('Task id=%s, status=%s, stdout=%s, stderr=%s',
                      task['id'], status, stdout, stderr)
            Tasks.update(task['id'], end=time.time())
            task_result = 'success' if status == 0 else 'failed'
        except Exception as e:
            LOG.exception(e)
            task_result = 'exception'
            stdout, stderr = '', e
        Tasks.update(task['id'], status='finished', result=task_result,
                     output=stdout or stderr)

        LOG.debug('end to deal with Task, id= %s' % task['id'])

    def sync(self):
        while not self.stop:
            thread_pool = threadpool.ThreadPool(5)
            LOG.info('sync start, check waiting tasks')
            for task in self.list_tasks(status='waiting'):
                thread_pool.spawn(self.execute_task, args=(task,))

            time.sleep(Manager.SYNC_INTERVAL)
