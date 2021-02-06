import os
import collections
import subprocess

from common import log

LOG = log.LOG


def log_steps(func):

    def foo(*args, **kwargs):
        LOG.debug("=== " + func.__doc__.split('\n')[0])
        return func(*args, **kwargs)

    return foo


def run_cmd(cmd):
    if isinstance(cmd, collections.abc.Iterable):
        cmd = ' '.join(cmd)
    LOG.debug('Run cmd: %s', cmd)
    status, stdout = subprocess.getstatusoutput(cmd)
    LOG.debug('Status: %s, stdout: %s', status, stdout)
    return status, stdout


def run_openstack_cmd(openrc, cmd):
    return run_cmd(
        ['source', openrc, '&&', 'openstack'] + cmd)


def yum_install(packages, download_dir=None):
    status, stdout = run_cmd(['rpm', '-q'] + packages)
    if status == 0:
        LOG.warning('packages have been installed')
        return
    LOG.debug('download packages %s', packages)
    download_dir = os.path.join(
        'rpm_packages', download_dir or '_'.join(packages)
    )

    status, stdout = run_cmd(['yum', 'install', '--downloadonly',
                              '--downloaddir', download_dir] + packages)
    if status != 0:
        raise Exception("download packages failed, {0}".format(stdout))
    LOG.debug('install packages %s', packages)
    status, stdout = run_cmd(
        ['yum', 'install', '-y', download_dir + '/*.rpm']
    )
    if status != 0 and 'Error: Nothing to do' not in stdout:
        raise Exception("install packages failed")


def yum_remove(packages):
    """Remove Packages
    """
    status, stdout = run_cmd(['yum', 'remove', '-y'] + packages)
    if status != 0:
        raise Exception('remove packages failed')


def systemctl(action, service):
    LOG.debug('%s %s', action, service)
    return run_cmd(['systemctl', action, service])


def rm_path(path_list):
    return run_cmd(['rm', '-rf'] + path_list)


def stop_services(services):
    for service in services:
        status, _ = systemctl('status', service)
        if status == 4:
            continue
        LOG.debug("stopping service %s", service)
        status, stdout = systemctl('stop', service)
        if status != 0:
            LOG.error('stop %s failed', service)


def openstack_config_set(file_path, section, option, value):
    status, stdout = run_cmd(
        ['openstack-config', '--set', file_path, section, option, str(value)]
    )
    if status != 0:
        raise Exception('config database connection failed')


def rabbitmqctl_add_user(user, password, permissions=None):
    """
    :param user:
    :param password:
    :param permissions:
    :return:
    """
    LOG.debug('add user int rabbitmq %s', user)
    status, stdout = run_cmd(
        ['rabbitmqctl', 'add_user', user, password]
    )
    if status != 0:
        raise Exception('add user failed')
    LOG.debug('set user permissions')
    if permissions:
        run_cmd(['rabbitmqctl', 'set_permissions', user,
                 '{0}'.format(permissions)])


def openstack_config(config_file, section, configs):
    for option, value in configs.items():
        openstack_config_set(config_file, section,
                             option, '\'{0}\''.format(value))
        # print(config_file, section, option, value)

