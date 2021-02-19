import os
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as v3client


def make_v3_client(**kwargs):
    """
    kwargs:
        auth_url
        username
        password
        project_name
        user_domain_name
        project_domain_name
    """
    auth_kwargs = {}
    for auth_arg in ['auth_url', 'username', 'password', 'project_name',
                     'user_domain_name', 'project_domain_name']:
        auth_kwargs[auth_arg] = os.environ.get(
            'OS_{0}'.format(auth_arg.upper())
        )
    auth_kwargs.update(**kwargs)
    auth = v3.Password(**auth_kwargs)
    auth_session = session.Session(auth=auth)
    return v3client.Client(session=auth_session)


keystone = make_v3_client()
print(keystone.users.list())