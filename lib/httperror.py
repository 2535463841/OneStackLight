from simplelib.common.exceptions import UnknownException


class Unauthorized(UnknownException):
    _message = 'Unauthorized'

    def __init__(self):
        super(Unauthorized, self).__init__()


class Http404Error(UnknownException):
    _message = 'url={url}, resp={resp}'

    def __init__(self, **kwargs):
        super(Http404Error, self).__init__(**kwargs)
