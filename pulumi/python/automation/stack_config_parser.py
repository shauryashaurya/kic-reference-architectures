import os
import typing
from typing import Union, Any, Dict, List, Hashable

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class PulumiStackConfig:
    yaml_data: Union[Union[Dict[Hashable, Any], List[Any], None], Any]

    def __init__(self, yaml_data: Union[Union[Dict[Hashable, Any], List[Any], None], Any]) -> None:
        super().__init__()
        self.yaml_data = yaml_data

    def __iter__(self):
        return self.yaml_data.__iter__()


def read(config_file_path: str) -> PulumiStackConfig:
    with open(config_file_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
        return PulumiStackConfig(yaml_data=yaml_data)
