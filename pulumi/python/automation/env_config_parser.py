import os
import typing
from configparser import ConfigParser

import stack_config_parser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.abspath(os.path.sep.join([SCRIPT_DIR, '..', '..', '..', 'config', 'pulumi', 'environment']))


class EnvConfigParser(ConfigParser):
    _config_file_path: typing.Optional[str] = None
    _stack_config: typing.Optional[stack_config_parser.PulumiStackConfig] = None

    def __init__(self) -> None:
        super().__init__()
        self.optionxform = lambda option: option

    def init(self, config_file_path: str = DEFAULT_PATH):
        self._config_file_path = config_file_path
        with open(config_file_path, 'r') as f:
            content = f'[main]{os.linesep}{f.read()}'
            self.read_string(content)

    def stack_name(self) -> str:
        return self.get(section='main', option='PULUMI_STACK')

    def main_section(self) -> typing.Mapping[str, str]:
        return self['main']

    def stack_config(self) -> stack_config_parser.PulumiStackConfig:
        if not self._stack_config:
            config_dir = os.path.dirname(self._config_file_path)
            stack_config_path = os.path.sep.join([config_dir, f'Pulumi.{self.stack_name()}.yaml'])
            self._stack_config = stack_config_parser.read(stack_config_path)

        return self._stack_config
