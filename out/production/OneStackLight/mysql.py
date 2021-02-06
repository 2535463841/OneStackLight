from common import manager
from common import utils
from common import baseinstaller


@manager.register_service('mariadb')
class MariadbCentosInstaller(baseinstaller.BaseCentosInstaller):
    PACKAGES = ['mariadb', 'mariadb-server']
    SERVICES = ['mariadb']

    def __init__(self):
        super().__init__()
        self.cleanup_resources = ["/var/lib/mysql", '/var/log/mariadb/']

    @utils.log_steps
    def clean_up(self):
        """Clean Up Mariadb Data
        """
        utils.rm_path(self.cleanup_resources)

    def update_config_files(self):
        pass

    def create_authorization(self):
        pass

    def init_database(self):
        pass

    def update_database(self):
        pass
