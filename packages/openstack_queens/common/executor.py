import locale
import logging
import subprocess

LOG = logging.getLogger(__name__)


def read_stream(stream):
    lines = []
    line = stream.readline()
    while line:
        lines.append(str(line, locale.getpreferredencoding()))
        line = stream.readline()
    return ''.join(lines)


class LinuxExecutor(object):

    @classmethod
    def execute(cls, cmd, stdout=None, stderr=None):
        execute_cmd = cmd[:]
        if isinstance(stdout, str):
            execute_cmd.append('1>{0}'.format(stdout))
        if isinstance(stderr, str):
            execute_cmd.extend('2>{0}'.format(stderr))

        execute_cmd = ' '.join(execute_cmd)
        LOG.debug('Execute: %s', execute_cmd)
        p = subprocess.Popen(execute_cmd, shell=True)
        out = read_stream(p.stdout)
        err = read_stream(p.stderr)
        p.communicate()
        LOG.debug('Stdout: %s, Stderr: %s', out, err)
        return p.returncode, ''.join(out), ''.join(err)


class CentosExecutor(LinuxExecutor):

    @classmethod
    def yum(cls, options):
        return cls.execute(['yum'] + options)

    @classmethod
    def rpm(cls, options):
        return cls.execute(['rpm'] + options)

