from typing import List

from .base_provider import PulumiProject, Provider


class AwsProvider(Provider):
    def infra_execution_order(self) -> List[PulumiProject]:
        return [
            PulumiProject(path='infrastructure/aws/vpc', description='VPC'),
            PulumiProject(path='infrastructure/aws/eks', description='EKS'),
            PulumiProject(path='infrastructure/aws/ecr', description='ECR')
        ]


INSTANCE = AwsProvider()
