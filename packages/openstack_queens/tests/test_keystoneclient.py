import unittest
import time

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

from common.lib import keystone


class TestKeystoneClient(unittest.TestCase):

    def setUp(self):
        self.client = keystone.KeystoneV3(
            auth_url="http://197.168.137.100:5000/v3",
            username="admin",
            password="admin1234",
            project_name="admin",
            user_domain_name="default",
            project_domain_name="default"
        )
        self.sufix = time.time()

    def test_user_create(self):
        project_name = 'project_{0}'.format(self.sufix)
        user_name = 'user_{0}'.format(self.sufix)
        role_name = 'role_{0}'.format(self.sufix)

        role = self.client.get_or_create_role(role_name)
        # self.addCleanup(self.client.keystone.roles.delete, role.id)

        project = self.client.get_or_create_project(project_name, 'default')
        # self.addCleanup(self.client.keystone.projects.delete, project.id)
        self.assertEqual(project.name, project_name)

        user = self.client.get_or_create_user(
            user_name, 'default', project_name, 
            role_name=role_name)

        # self.addCleanup(self.client.keystone.users.delete, user.id)
        self.assertEqual(user.name, user_name)

