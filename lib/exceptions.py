
class UnknownException(Exception):
    _message = 'Unknown exception'

    def __init__(self, **kwargs):
        super(UnknownException, self).__init__(
            self._message.format(**kwargs)
        )
