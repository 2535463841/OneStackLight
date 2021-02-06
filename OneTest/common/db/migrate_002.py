import os
import peewee
import sys
from playhouse.migrate import *

if os.getcwd() not in sys.path:  # noqa
    sys.path.append(os.getcwd())  # noqa

from common.db import models

migrator = SqliteMigrator(models.DB)
migrate(
    # migrator.drop_column('tasks', 'output'),
    migrator.add_column('tasks', 'output', peewee.TextField(default='')),
)
