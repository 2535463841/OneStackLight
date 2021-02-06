import commands


class BaseShellCmd(object):

    def exec_command(self, cmd, expect_code=None):
        cmd = ' '.join(cmd)
        status, output = commands.getstatusoutput(cmd)
        if expect_code and status != expect_code:
            raise Exception('execute command failed: {}', cmd)
        return output


class Systemctl(BaseShellCmd):
    BASH = 'systemctl'

    def is_active(self, service):
        cmd = [self.BASH, 'is-active', service]
        return self.exec_command(cmd)
