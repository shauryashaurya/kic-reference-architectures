import os

from kic_util import external_process
from typing import List, Optional, MutableMapping

from pulumi import automation as auto

from .base_provider import PulumiProject, Provider, InvalidConfigurationException

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class AwsProviderException(Exception):
    pass


class AwsCli:
    region: str
    profile: str

    def __init__(self, region: Optional[str] = None, profile: Optional[str] = None):
        super().__init__()
        self.region = region
        self.profile = profile

    def base_cmd(self) -> str:
        cmd = 'aws '
        if self.region:
            cmd += f'--region {self.region} '
        if self.profile:
            cmd += f'--profile {self.profile} '
        return cmd.strip()

    def update_kubeconfig_cmd(self, cluster_name: str) -> str:
        """
        Returns the command used to update the kubeconfig with the passed cluster
        :param cluster_name: name of the cluster to add to the kubeconfig
        :return: command to be executed
        """
        return f'{self.base_cmd()} eks update-kubeconfig --name {cluster_name}'

    def validate_aws_credentials_cmd(self) -> str:
        """
        Returns the command used to verify that AWS has valid credentials
        :return: command to be executed
        """
        return f'{self.base_cmd()} sts get-caller-identity'


class AwsProvider(Provider):
    def infra_execution_order(self) -> List[PulumiProject]:
        return [
            PulumiProject(root_path='infrastructure/aws/vpc', description='VPC'),
            PulumiProject(root_path='infrastructure/aws/eks', description='EKS',
                          on_success=AwsProvider._update_kubeconfig),
            PulumiProject(root_path='infrastructure/aws/ecr', description='ECR')
        ]

    def validate_stack_config(self, config: MutableMapping[str, auto._config.ConfigValue]):
        super().validate_stack_config(config)
        if 'aws:region' not in config:
            raise InvalidConfigurationException('When using the AWS provider, the region must be specified')

        aws_cli = AwsCli(region=config.get('aws:region').value, profile=config.get('aws:profile').value)
        try:
            _, err = external_process.run(cmd=aws_cli.validate_aws_credentials_cmd())
        except Exception as e:
            raise AwsProviderException('Unable to authenticate against AWS') from e

    def extract_pulumi_config_to_apply(self, env_config) -> MutableMapping[str, auto.ConfigValue]:
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
                                      stack_config_key: str) -> Optional[str]:
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

    @staticmethod
    def _update_kubeconfig(stack_outputs: MutableMapping[str, auto._output.OutputValue],
                           config: MutableMapping[str, auto._config.ConfigValue]):
        if 'cluster_name' not in stack_outputs:
            raise AwsProviderException('Cannot find key [cluster_name] in stack output')

        aws_cli = AwsCli(region=config.get('aws:region').value, profile=config.get('aws:profile').value)
        cluster_name = stack_outputs['cluster_name'].value
        cmd = aws_cli.update_kubeconfig_cmd(cluster_name)
        res, err = external_process.run(cmd)
        print(res)

INSTANCE = AwsProvider()
