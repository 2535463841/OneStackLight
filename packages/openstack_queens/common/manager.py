
SERVICE_SUPPORTED = {}


def register_service(name):

    def foo(cls):
        if name in SERVICE_SUPPORTED:
            raise Exception(
                'register {0} failed, name={1} already exists'.format(
                    cls, name)
            )
        SERVICE_SUPPORTED[name] = cls
        return cls

    return foo
