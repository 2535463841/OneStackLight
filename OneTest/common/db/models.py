import peewee

from common import config

CONF = config.CONF
DB = peewee.SqliteDatabase(CONF.sqlite.connection)


class BaseModel(peewee.Model):
    class Meta:
        database = DB

    id = peewee.PrimaryKeyField()


class TestCases(BaseModel):
    name = peewee.CharField(100)
    cmd = peewee.TextField()
    description = peewee.TextField()


class TestProject(BaseModel):
    name = peewee.CharField(100)


class Tasks(BaseModel):
    case = peewee.ForeignKeyField(TestCases)
    project = peewee.ForeignKeyField(TestProject)
    options = peewee.CharField(200, default='')
    status = peewee.CharField(100, default='waiting',
                              choices=['waiting', 'running', 'finished'])
    result = peewee.CharField(100, null=True, default='',
                              choices=['', 'success', 'failed', 'exception', 'canceled'])
    start = peewee.DateTimeField(null=True)
    end = peewee.DateTimeField(null=True)
    output = peewee.TextField(default='')


TestCases.create_table()
TestProject.create_table()
Tasks.create_table()
