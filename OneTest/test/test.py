# -*- coding: utf-8 -*-

import os
import sys
import time
import unittest


if os.getcwd() not in sys.path:  # noqa
    sys.path.append(os.getcwd())  # noqa

from common.db import models
from common import manager
from simplelib.linux.executor import LinuxExecutor

class TestTasks(unittest.TestCase):

    def test_tasks_create(self):
        task = models.Tasks.create(
            project_id='4', case_id='101', status='waiting', output='xx', result='finished', options='a b c',
            end=time.time()
        )
        print(task.__str__())


if __name__ == '__main__':
    # unittest.main()
    print(
        dict([('a', 1), ('b', 2)])
    )
