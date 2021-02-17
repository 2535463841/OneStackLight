from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from keystoneclient.v3.projects import Project


class KeystoneV3:

    def __init__(self, *args, **kwargs) -> None:
        auth = v3.Password(*args, **kwargs)
        sess = session.Session(auth=auth)
        self.keystone = client.Client(session=sess)

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

        print('role_name=', role_name)
        if role_name:
            role = self.get_or_create_role(role_name)
            print('role=', role)
            self.keystone.roles.grant(role, user=user, project=project)
        return user
