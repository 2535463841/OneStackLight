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
        status, _ = utils.run_cmd([
            'source', self.admin_openrc, '&&',
            'openstack', 'project', 'create', self.test_user_project,
            '--domain', 'default', '--description', '"Test Project"'
        ])
        self.assertEqual(status, 0, 'create test project failed')
        self.addCleanup(
            utils.run_cmd,
            ['openstack', 'project', 'delete', self.test_user_project]
        )

    def create_user(self):
        status, _ = utils.run_cmd([
            'source', self.admin_openrc, '&&',
            'openstack', 'user', 'create', self.test_user_name,
            '--project', self.test_user_project,
            '--password', self.test_user_password,
        ])
        self.assertEqual(status, 0, 'create test user failed')
        self.addCleanup(
            utils.run_openstack_cmd,
            self.admin_openrc,
            ['user', 'delete', self.test_user_name]
        )

    def test_create_project(self):
        self.create_project()
        self.addCleanup(
            utils.run_cmd,
            ['openstack', 'project', 'delete', self.test_user_project]
        )

    def test_create_user(self):
        self.create_project()
        self.create_user()

    def test_create_role(self):
        self.create_project()
        self.create_user()

        status, _ = utils.run_cmd([
            'source', self.admin_openrc, '&&',
            'openstack', 'role', 'create', self.test_user_role,
        ])
        self.assertEqual(status, 0, 'create test role failed')
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
