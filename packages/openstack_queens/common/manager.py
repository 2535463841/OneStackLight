import os
import logging


from common.executor import CentosExecutor


SERVICE_SUPPORTED = {}

LOG = logging.getLogger(__name__)


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


class CentosManager:

    @classmethod
    def install_packages(cls, packages, download_dir=None):
        status, stdout, _ = CentosExecutor.rpm(['-q'] + packages)
        if status == 0:
            LOG.warning('packages have been installed')
            return
        LOG.debug('download packages %s', packages)
        download_dir = os.path.join(
            'rpm_packages', download_dir or '_'.join(packages)
        )

        status, stdout, _ = CentosExecutor.yum(
            ['install', '--downloadonly',
             '--downloaddir', download_dir] + packages
        )
        if status != 0:
            raise Exception("download packages failed, {0}".format(stdout))

        LOG.debug('install packages %s', packages)
        status, stdout = CentosExecutor.yum(
            ['install', '-y', download_dir + '/*.rpm']
        )
        if status != 0 and 'Error: Nothing to do' not in stdout:
            raise Exception("install packages failed")

    @classmethod
    def remove_packages(cls, packages):
        return CentosExecutor.yum(['remove'] + packages)
