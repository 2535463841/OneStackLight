import locale
import logging
import subprocess

LOG = logging.getLogger(__name__)


def read_stream(stream):
    if not stream:
        return ''
    lines = []
    line = stream.readline()
    while line:
        lines.append(str(line, locale.getpreferredencoding()))
        line = stream.readline()
    return ''.join(lines)


class LinuxExecutor(object):

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def execute(self, options, stdout=None, stderr=None):
        execute_cmd =  options[:]
        if isinstance(stdout, str):
            execute_cmd.append('1>{0}'.format(stdout))
        if isinstance(stderr, str):
            execute_cmd.extend('2>{0}'.format(stderr))

        execute_cmd = '{0} {1}'.format(self.cmd, ' '.join(execute_cmd))
        LOG.debug('Execute: %s', execute_cmd)
        p = subprocess.Popen(execute_cmd, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = read_stream(p.stdout)
        err = read_stream(p.stderr)
        p.communicate()
        LOG.debug('Stdout: %s, Stderr: %s', out, err)
        return p.returncode, ''.join(out), ''.join(err)


class CentosExecutor(object):

    def __init__(self) -> None:
        super().__init__()
        self.yum = LinuxExecutor('yum')
        self.rpm = LinuxExecutor('rpm')
        self.chown = LinuxExecutor('chown')
        self.chmod = LinuxExecutor('chmod')
        self.ln = LinuxExecutor('ln')
