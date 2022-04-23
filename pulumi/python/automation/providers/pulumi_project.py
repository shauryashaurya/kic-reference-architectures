import os.path
import typing

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class PulumiConfigException(Exception):
    pass


class PulumiProject:
    root_path: str
    description: str
    _config_data: typing.Optional[typing.Mapping[str, str]] = None

    def __init__(self, root_path: str, description: str) -> None:
        super().__init__()
        self.root_path = root_path
        self.description = description

    def path(self) -> str:
        relative_path = os.path.sep.join([SCRIPT_DIR, '..', '..', self.root_path])
        return os.path.abspath(relative_path)

    def config(self) -> typing.Mapping[str, str]:
        if not self._config_data:
            config_path = os.path.sep.join([self.path(), 'Pulumi.yaml'])
            with open(config_path, 'r') as f:
                self._config_data = yaml.safe_load(f)

        return self._config_data

    def name(self) -> str:
        config_data = self.config()

        if 'name' not in config_data.keys():
            raise PulumiConfigException('Pulumi configuration did not contain required "name" key')

        return config_data['name']