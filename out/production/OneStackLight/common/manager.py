
SERVICE_SUPPORTED = {}


def register_service(name):

    def foo(cls):
        if name in SERVICE_SUPPORTED:
            raise Exception(
                'register installer failed, {0} already exists'.format(name)
            )
        SERVICE_SUPPORTED[name] = cls
        return cls

    return foo
