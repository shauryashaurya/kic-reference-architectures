#!env python3
import getopt
import importlib
import importlib.util
import os
import sys
import typing
import colorize
import env_config_parser
from typing import List, Optional
from fart import fart
from providers.base_provider import Provider
from pulumi import automation as auto

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPERATIONS: List[str] = ['down', 'refresh', 'show-execution', 'up']
PROVIDERS: typing.Iterable[str] = Provider.list_providers()
PROJECT_ROOT = os.path.abspath(os.path.sep.join([SCRIPT_DIR, '..']))
FART_FONT = fart.load_font('standard')

debug_on = False


def usage():
    usage_text = f"""Modern Application Reference Architecture (MARA) Runner

USAGE:
    main.py [FLAGS] [OPERATION]

FLAGS:
    -d, --debug     Enable debug output on all of the commands executed
    -h, --help      Prints help information
    -p, --provider= Specifies the provider used (e.g. {', '.join(PROVIDERS)})

OPERATIONS:
    down            Destroys all provisioned infrastructure
    list-providers  Lists all of the supported providers
    refresh         Refreshes the Pulumi state of all provisioned infrastructure
    show-execution  Displays the execution order of the Pulumi projects used to provision
    up              Provisions all configured infrastructure
"""
    print(usage_text)


def provider_instance(provider_name: str) -> Provider:
    module = importlib.import_module(name=f'providers.{provider_name}')
    return module.INSTANCE


def main():
    try:
        shortopts = 'hp:'
        longopts = ["help", 'provider=']
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError as err:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    provider_name: Optional[str] = None

    # Parse flags
    for opt, value in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-p', '--provider'):
            if value.lower() != 'none':
                provider_name = value.lower()

    # Make sure we got an operation - it is the last string passed as an argument
    if len(sys.argv) > 1:
        operation = sys.argv[-1]
    else:
        print(f'No operation specified')
        usage()
        sys.exit(2)

    # Start processing operations, first we process those that do not depend on providers
    if operation == 'list-providers':
        for provider in PROVIDERS:
            print(provider, file=sys.stdout)
        sys.exit(0)

    # Now validate providers because everything underneath here depends on them
    if provider_name not in PROVIDERS:
        print(f'Unknown provider specified: {provider_name}')
        sys.exit(2)

    provider = provider_instance(provider_name)

    if operation == 'show-execution':
        provider.display_execution_order(output=sys.stdout)
        sys.exit(0)

    env_config = env_config_parser.EnvConfigParser()
    env_config.init()
    provider.validate_env_config(env_config.main_section())

    if operation == 'refresh':
        refresh(provider, env_config)
    elif operation == 'up':
        up(provider, env_config)
    else:
        print(f'Unknown operation: {operation}')
        sys.exit(2)


def render_header(text: str):
    header = fart.render_fart(text=text, font=FART_FONT)
    colorize.PRINTLN_FUNC(header)


def refresh(provider: Provider, env_config: env_config_parser.EnvConfigParser):
    for pulumi_project in provider.execution_order():
        render_header(pulumi_project.description)
        print(f'project: {pulumi_project.name()} path: {pulumi_project.path()}')
        stack = auto.create_or_select_stack(stack_name=env_config.stack_name(),
                                            project_name=pulumi_project.name(),
                                            work_dir=pulumi_project.path())
        print(f'applying config: {provider.extract_pulumi_config_to_apply(env_config)}')
        stack.set_all_config(provider.extract_pulumi_config_to_apply(env_config))
        provider.validate_stack_config(stack.get_all_config())
        stack.refresh(on_output=print)

def up(provider: Provider, env_config: env_config_parser.EnvConfigParser):
    for pulumi_project in provider.execution_order():
        render_header(pulumi_project.description)
        print(f'project: {pulumi_project.name()} path: {pulumi_project.path()}')
        stack = auto.create_or_select_stack(stack_name=env_config.stack_name(),
                                            project_name=pulumi_project.name(),
                                            work_dir=pulumi_project.path())
        print(f'applying config: {provider.extract_pulumi_config_to_apply(env_config)}')
        stack.set_all_config(provider.extract_pulumi_config_to_apply(env_config))
        provider.validate_stack_config(stack.get_all_config())
        stackUpResult = stack.up(on_output=print)
        if pulumi_project.on_success:
            pulumi_project.on_success(stackUpResult.outputs, stack.get_all_config())


if __name__ == "__main__":
    main()
