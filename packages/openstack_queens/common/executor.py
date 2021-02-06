import locale
import logging
import subprocess

from simplelib.common.exceptions import UnknownException

LOG = logging.getLogger(__name__)


class CmdExecException(UnknownException):
    _message = 'execute cmd failed, status: {status} stderr: {stderr}'


def read_stream(stream):
    lines = []
    line = stream.readline()
    while line:
        lines.append(str(line, locale.getpreferredencoding()))
        line = stream.readline()
    return ''.join(lines)


class LinuxExecutor(object):

    def __init__(self, cmd):
        self.cmd = cmd
        self.options = []
        self._stdout = None
        self._stderr = None

    def with_options(self, *args):
        self.options.extend(list(args))
        return self

    def execute(self, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        cmd = [self.cmd] + self.options
        if self._stdout:
            cmd.extend(' 1>{0}'.format(self._stdout))
        if self._stderr:
            cmd.extend(' 2>{0}'.format(self._stdout))
        LOG.debug('>> %s', cmd)
        p = subprocess.Popen(' '.join(cmd),
                             shell=True, stdout=stdout, stderr=stderr)
        out = read_stream(p.stdout)
        err = read_stream(p.stderr)
        p.communicate()
        LOG.debug('Stdout: %s, Stderr: %s', out, err)
        return p.returncode, ''.join(out), ''.join(err)

    def stdout(self, file_path):
        self._stdout = file_path
        return self

    def stderr(self, file_path):
        self._stderr = file_path
        return self


class Ls(LinuxExecutor):

    def __init__(self):
        super(Ls, self).__init__('ls')

    def with_l(self):
        return self.with_options('-l')


class Which(LinuxExecutor):

    def __init__(self):
        super(Which, self).__init__('which')


class Ps(LinuxExecutor):

    def __init__(self):
        super(Ps, self).__init__('ps')

    def aux(self):
        return self.with_options('aux')


class Kill(LinuxExecutor):
    def __init__(self):
        super(Kill, self).__init__('kill')

    def with_9(self):
        super(Kill, self).with_options('-9')
