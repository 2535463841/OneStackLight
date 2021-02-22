import os

from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneclient.v3 import client

from neutronclient.v2_0 import client as neutrnoclient
from novaclient import client as novaclient



class OpenstackClient:
    """openstack clients

    >>> openstack = OpenstackClient.create_instance()
    >>> users = openstack.keystone.users.list()
    >>> len(users) > 0
    True
    """

    def __init__(self, *args, **kwargs):
        self.auth = v3.Password(*args, **kwargs)
        self.session = session.Session(auth=self.auth)
        self.keystone = client.Client(session=self.session)
        self.neutron = neutrnoclient.Client(session=self.session)
        self.nova = novaclient.Client('2.0', session=self.session)

    @classmethod
    def create_instance(cls, *kwargs):
        auth_url = os.environ.get('OS_AUTH_URL')
        auth_params = {
            'username': os.environ.get('OS_USERNAME'),
            'password': os.environ.get('OS_PASSWORD'),
            'project_name': os.environ.get('OS_PROJECT_NAME'),
            'user_domain_name': os.environ.get('OS_USER_DOMAIN_NAME'),
            'project_domain_name': os.environ.get('OS_PROJECT_DOMAIN_NAME'),
        }
        auth_params.update(kwargs)
        return cls(auth_url, **auth_params)

    def get_or_create_domain(self, name):
        domains = self.keystone.domains.list(name=name)
        return domains[0] if domains else self.keystone.domains.create(name)
    
    def get_or_create_role(self, name, domain_name=None):
        domain = None
        if domain_name:
            domain = self.get_or_create_domain(domain_name)
        roles = self.keystone.roles.list(name=name, domain=domain)
        return roles[0] if roles else self.keystone.roles.create(
            name, domain=domain)
    
    def get_or_create_project(self, name, domain_name, **kwargs):
        domain = self.get_or_create_domain(domain_name)
        projects = self.keystone.projects.list(name=name, domain=domain)
        return projects[0] if projects else self.keystone.projects.create(
            name, domain, **kwargs)

    def get_or_create_user(self, name, domain_name, projec_name, **kwargs):
        domain = self.get_or_create_domain(domain_name)
        project = self.get_or_create_project(projec_name, domain_name)
        role_name = kwargs.pop('role_name', None)
        users = self.keystone.users.list(name=name, domain=domain)
        user = users[0] if users else self.keystone.users.create(
            name, domain=domain, project=project, **kwargs
        )

        if role_name:
            role = self.get_or_create_role(role_name)
            self.keystone.roles.grant(role, user=user, project=project)
        return user
