import os
import uuid
import unittest

from common import utils


class TestKeystoneInstall(unittest.TestCase):
    """Test Keystone Functions With Openstack CLI
    """

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        self.admin_openrc = os.path.join(os.path.expanduser('~'), 'admin_openrc')
        self.assertTrue(os.path.exists(self.admin_openrc),
                        'admin_openrc file not found ')
        test_uuid = uuid.uuid4()
        self.test_user_project = 'project-{0}'.format(test_uuid)
        self.test_user_name = 'user-{0}'.format(test_uuid)
        self.test_user_role = 'role-{0}'.format(test_uuid)
        self.test_user_password = 'test@{0}'.format(test_uuid)

    def create_project(self):
        status, stdout = utils.run_cmd([
            'source', self.admin_openrc, '&&',
            'openstack', 'project', 'create', self.test_user_project,
            '--domain', 'default', '--description', '"Test Project"'
        ])
        self.addCleanup(
            utils.run_openstack_cmd,
            self.admin_openrc,
            ['project', 'delete', self.test_user_project]
        )
        return status, stdout

    def create_user(self):
        status, stdout = utils.run_openstack_cmd(
            self.admin_openrc,
            ['user', 'create', self.test_user_name,
            '--project', self.test_user_project,
            '--password', self.test_user_password,
            '--domain', 'domain'
        ])
        print()
        self.addCleanup(
            utils.run_openstack_cmd,
            self.admin_openrc,
            ['user', 'delete', self.test_user_name]
        )
        return status, stdout

    def test_create_project_user_role(self):
        status, stdout = self.create_project()
        self.assertEqual(status, 0, 'create project failed')
        status, stdout = self.create_user()
        self.assertEqual(status, 0, 'create user failed')

        status, _ = utils.run_cmd([
            'source', self.admin_openrc, '&&',
            'openstack', 'role', 'create', self.test_user_role,
        ])
        self.assertEqual(status, 0, 'create role failed')
        self.addCleanup(
            utils.run_openstack_cmd,
            self.admin_openrc,
            ['role', 'delete', self.test_user_role]
        )
        status, _ = utils.run_cmd([
            'source', self.admin_openrc, '&&',
            'openstack', 'role', 'add', '--project', self.test_user_project,
            '--user', self.test_user_name, self.test_user_role,
        ])
        self.assertEqual(status, 0, 'add role failed')

    def test_token_issue(self):
        status, _ = utils.run_cmd([
            'source', self.admin_openrc, '&&', 'openstack', 'token', 'issue'
        ])
        self.assertEqual(status, 0, 'token issue failed')

    def test_show_admin(self):
        status, _ = utils.run_cmd(['source', self.admin_openrc, '&&',
                                   'openstack', 'user', 'show', 'admin'
        ])
        self.assertEqual(status, 0, 'show admin failed')
