import os
import yaml
import configparser


from common import manager
from common import baseinstaller


@manager.register_service('mariadb')
class MemcachedCentosInstaller(baseinstaller.BaseCentosInstaller):

    def update_config_files(self):
        config_files = self.conf.get('config_files')
        for config_file in config_files:
            parser = configparser.ConfigParser()
            for section, options in config_file.get('configs').items():
                parser.add_section(section)
                for key, value in options.items():
                    parser.set(section, key, str(value))
            with open(config_file.get('file'), 'w') as f:
                parser.write(f)
