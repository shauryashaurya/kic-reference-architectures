import abc
import os
import pathlib
import sys
from typing import List, Mapping, MutableMapping, Iterable, TextIO, Union, Dict, Any, Hashable, Callable, Optional

from pulumi import automation as auto

from .pulumi_project import PulumiProject

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class InvalidConfigurationException(Exception):
    pass


class Provider:
    @staticmethod
    def list_providers() -> Iterable[str]:
        def is_provider(file: pathlib.Path) -> bool:
            return file.is_file() and \
                   not file.stem.endswith('base_provider') and \
                   not file.stem.endswith('pulumi_project')

        path = pathlib.Path(SCRIPT_DIR)
        return [os.path.splitext(file.stem)[0] for file in path.iterdir() if is_provider(file)]

    @staticmethod
    def validate_env_config_required_keys(required_keys: List[str], config: Mapping[str, str]):
        for key in required_keys:
            if key not in config.keys():
                raise InvalidConfigurationException(f'Required configuration key [{key}] not found')

    @abc.abstractmethod
    def infra_execution_order(self) -> List[PulumiProject]:
        pass

    def new_stack_config(self, env_config, defaults: Union[Dict[Hashable, Any], list, None]) -> \
            Union[Dict[Hashable, Any], list, None]:
        return {}

    def validate_env_config(self, config: Mapping[str, str]):
        Provider.validate_env_config_required_keys(['PULUMI_STACK'], config)

    def validate_stack_config(self, stack_config: Union[Dict[Hashable, Any], list, None]):
        pass

    def k8s_execution_order(self) -> List[PulumiProject]:
        return [
            PulumiProject(path='infrastructure/kubeconfig', description='Kubeconfig'),
            PulumiProject(path='utility/kic-image-build', description='KIC Image Build'),
            PulumiProject(path='utility/kic-image-push', description='KIC Image Build'),
            PulumiProject(path='kubernetes/nginx/ingress-controller', description='Ingress Controller'),
            PulumiProject(path='kubernetes/logstore', description='Logstore'),
            PulumiProject(path='kubernetes/logagent', description='Log Agent'),
            PulumiProject(path='kubernetes/certmgr', description='Cert Manager'),
            PulumiProject(path='kubernetes/prometheus', description='Prometheus'),
            PulumiProject(path='kubernetes/observability', description='Observability'),
            PulumiProject(path='kubernetes/applications/sirius', description='Bank of Sirius')
        ]

    def execution_order(self) -> List[PulumiProject]:
        return self.infra_execution_order() + self.k8s_execution_order()

    def display_execution_order(self, output: TextIO = sys.stdout):
        execution_order = self.execution_order()
        last_prefix = ''

        for index, pulumi_project in enumerate(execution_order):
            path_parts = pulumi_project.root_path.split(os.path.sep)
            project = f'{path_parts[-1]} [{pulumi_project.description}]'
            prefix = os.path.sep.join(path_parts[:-1])

            # First item in the list
            if last_prefix != prefix and index == 0:
                print(f' ┌── {prefix}', file=output)
                print(f' │   ├── {project}', file=output)
            # Last item in the list with a new prefix
            elif last_prefix != prefix and index == len(execution_order) - 1:
                print(f' └── {prefix}', file=output)
                print(f'     └── {project}', file=output)
            # Any other item with a new prefix
            elif last_prefix != prefix and index != 0:
                print(f' ├── {prefix}', file=output)

                peek = execution_order[index + 1]
                splitted = peek.root_path.split(f'{prefix}{os.path.sep}')[0]
                # item is not the last item with the prefix
                if os.path.sep not in splitted:
                    print(f' │   ├── {project}', file=output)
                # item is the last item with the prefix
                else:
                    print(f' │   └── {project}', file=output)
            elif last_prefix == prefix:
                print(f' │   ├── {project}', file=output)
            elif last_prefix == prefix and index == len(execution_order) - 1:
                print(f' │   └── {project}', file=output)

            if last_prefix != prefix:
                last_prefix = prefix