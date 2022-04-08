import abc
import io
import os
import pathlib
import sys
import typing
from collections import namedtuple
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PulumiProject = namedtuple('PulumiProject', ['path', 'description'])


class Provider:
    @staticmethod
    def list_providers() -> typing.Iterable[str]:
        def is_provider(file: pathlib.Path) -> bool:
            return file.is_file() and not file.stem.endswith('base_provider')

        path = pathlib.Path(SCRIPT_DIR)
        return [os.path.splitext(file.stem)[0] for file in path.iterdir() if is_provider(file)]

    @abc.abstractmethod
    def infra_execution_order(self) -> List[PulumiProject]:
        pass

    def k8s_execution_order(self) -> List[PulumiProject]:
        return [
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

    def display_execution_order(self, output: typing.TextIO = sys.stdout):
        execution_order = self.execution_order()
        last_prefix = ''

        for index, pulumi_project in enumerate(execution_order):
            path_parts = pulumi_project.path.split(os.path.sep)
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
                splitted = peek.path.split(f'{prefix}{os.path.sep}')[0]
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