from common import manager
from common import baseinstaller


@manager.register_service('memcached')
class CacheMemCentosInstaller(baseinstaller.BaseCentosInstaller):

    def clean_up(self):
        pass

    def update_config_files(self):
        pass

    def create_authorization(self):
        pass

    def init_database(self):
        pass

    def update_database(self):
        pass
