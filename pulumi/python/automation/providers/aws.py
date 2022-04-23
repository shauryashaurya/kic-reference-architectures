import typing
from typing import List

from pulumi import automation as auto

from .base_provider import PulumiProject, Provider, InvalidConfigurationException


class AwsProvider(Provider):
    def infra_execution_order(self) -> List[PulumiProject]:
        return [
            PulumiProject(root_path='infrastructure/aws/vpc', description='VPC'),
            PulumiProject(root_path='infrastructure/aws/eks', description='EKS'),
            PulumiProject(root_path='infrastructure/aws/ecr', description='ECR')
        ]

    def extract_pulumi_config_to_apply(self, env_config) -> typing.MutableMapping[str, auto.ConfigValue]:
        configs_to_apply = super().extract_pulumi_config_to_apply(env_config)

        aws_profile = AwsProvider._reconcile_conflicting_config(env_config, 'AWS_PROFILE', 'aws:profile')
        if aws_profile:
            configs_to_apply['aws:profile'] = auto.ConfigValue(value=aws_profile, secret=False)

        aws_region = AwsProvider._find_aws_region(env_config)
        configs_to_apply['aws:region'] = auto.ConfigValue(value=aws_region, secret=False)

        return configs_to_apply

    @staticmethod
    def _reconcile_conflicting_config(env_config,
                                      env_config_key: str,
                                      stack_config_key: str) -> typing.Optional[str]:
        envcfg = env_config.main_section()
        stackcfg = env_config.stack_config()

        env_file_has_profile = env_config_key in envcfg
        stack_config_has_profile = stack_config_key in stackcfg

        if env_file_has_profile and not stack_config_has_profile:
            return envcfg[env_config_key]
        if stack_config_has_profile and not env_file_has_profile:
            return stackcfg[stack_config_key]
        if not stack_config_has_profile and not env_file_has_profile:
            return None
        if stack_config_has_profile and env_file_has_profile:
            if envcfg[env_config_key] != stackcfg[stack_config_key]:
                raise InvalidConfigurationException('Conflicting AWS profile settings found between environment '
                                                    'file configuration and stack configuration file: '
                                                    f'{env_config_key}={env_config[env_config_key]} '
                                                    f'{stack_config_key}={stackcfg[stack_config_key]}')
            else:
                return envcfg['AWS_PROFILE']

    @staticmethod
    def _find_aws_region(env_config) -> str:
        envcfg = env_config.main_section()
        stackcfg = env_config.stack_config()

        if 'aws:region' in stackcfg:
            return stackcfg['aws:region']
        elif 'AWS_DEFAULT_REGION' in envcfg:
            return envcfg['AWS_DEFAULT_REGION']
        else:
            raise InvalidConfigurationException('AWS region was not specified in configuration')


INSTANCE = AwsProvider()
