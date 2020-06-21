from typing import List

from provider.vpc.command import VpcOptions
from shared.common import (
    ResourceProvider,
    Resource,
    message_handler,
    ResourceDigest,
    ResourceEdge,
    resource_tags,
)
from shared.common_aws import describe_subnet
from shared.error_handler import exception


class SAGEMAKERNOTEBOOK(ResourceProvider):
    def __init__(self, vpc_options: VpcOptions):
        """
        Sagemaker notebook instance

        :param vpc_options:
        """
        super().__init__()
        self.vpc_options = vpc_options

    @exception
    def get_resources(self) -> List[Resource]:

        client = self.vpc_options.client("sagemaker")

        resources_found = []

        response = client.list_notebook_instances()

        message_handler(
            "Collecting data from Sagemaker Notebook instances...", "HEADER"
        )

        for data in response["NotebookInstances"]:

            notebook_instance = client.describe_notebook_instance(
                NotebookInstanceName=data["NotebookInstanceName"]
            )
            tags_response = client.list_tags(ResourceArn=data["NotebookInstanceArn"],)

            # Using subnet to check VPC
            subnets = describe_subnet(
                vpc_options=self.vpc_options, subnet_ids=notebook_instance["SubnetId"]
            )

            if subnets is not None:
                if subnets["Subnets"][0]["VpcId"] == self.vpc_options.vpc_id:
                    sagemaker_notebook_digest = ResourceDigest(
                        id=data["NotebookInstanceArn"],
                        type="aws_sagemaker_notebook_instance",
                    )
                    resources_found.append(
                        Resource(
                            digest=sagemaker_notebook_digest,
                            name=data["NotebookInstanceName"],
                            details="",
                            group="ml",
                            tags=resource_tags(tags_response),
                        )
                    )

                    self.relations_found.append(
                        ResourceEdge(
                            from_node=sagemaker_notebook_digest,
                            to_node=ResourceDigest(
                                id=notebook_instance["SubnetId"], type="aws_subnet"
                            ),
                        )
                    )

        return resources_found


class SAGEMAKERTRAININGOB(ResourceProvider):
    def __init__(self, vpc_options: VpcOptions):
        """
        Sagemaker training job

        :param vpc_options:
        """
        super().__init__()
        self.vpc_options = vpc_options

    @exception
    def get_resources(self) -> List[Resource]:

        client = self.vpc_options.client("sagemaker")

        resources_found = []

        response = client.list_training_jobs()

        message_handler("Collecting data from Sagemaker Training Job...", "HEADER")

        for data in response["TrainingJobSummaries"]:
            tags_response = client.list_tags(ResourceArn=data["TrainingJobArn"],)
            training_job = client.describe_training_job(
                TrainingJobName=data["TrainingJobName"]
            )

            if "VpcConfig" in training_job:

                for subnets in training_job["VpcConfig"]["Subnets"]:

                    # Using subnet to check VPC
                    subnet = describe_subnet(
                        vpc_options=self.vpc_options, subnet_ids=subnets
                    )

                    if subnet is not None:

                        if subnet["Subnets"][0]["VpcId"] == self.vpc_options.vpc_id:

                            sagemaker_trainingjob_digest = ResourceDigest(
                                id=data["TrainingJobArn"],
                                type="aws_sagemaker_training_job",
                            )
                            resources_found.append(
                                Resource(
                                    digest=sagemaker_trainingjob_digest,
                                    name=data["TrainingJobName"],
                                    details="",
                                    group="ml",
                                    tags=resource_tags(tags_response),
                                )
                            )

                            self.relations_found.append(
                                ResourceEdge(
                                    from_node=sagemaker_trainingjob_digest,
                                    to_node=ResourceDigest(
                                        id=subnets, type="aws_subnet"
                                    ),
                                )
                            )

        return resources_found
