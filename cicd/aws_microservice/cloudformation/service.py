import argparse
import boto3
from awacs.aws import PolicyDocument, Statement, Allow, Action, Principal
from troposphere import Template, Ref, ImportValue
from troposphere import ecs, iam, logs, elasticloadbalancingv2


class GenECSService(object):
    IAM_POLICY_DOCUMENT_VERSION = "2012-10-17"

    def __init__(self, output_file):
        self.init_template()
        self.service_name = "conducto-demo-service"
        self.gen_cluster()
        self.gen_log_group()
        self.gen_execution_role()
        self.gen_task_role()
        self.gen_task_definition()
        self.gen_target_group()
        self.gen_listener_rule()
        self.gen_service()
        self.write_template(output_file)

    def init_template(self):
        self.template = Template(Description="ecs service")

    def write_template(self, output_file):
        with open(output_file, "w") as f:
            f.write(self.template.to_yaml())

    def import_value(self, stack_name, value_name):
        return ImportValue(f"conducto-demo-{stack_name}-{value_name}")

    def gen_cluster(self):
        self.cluster = ecs.Cluster("ECSCluster", ClusterName="conducto-demo-cluster")
        self.template.add_resource(self.cluster)

    def gen_log_group(self):
        self.log_group_name = "conducto-demo-log-group"
        log_group = logs.LogGroup(
            "LogGroup", LogGroupName=self.log_group_name, RetentionInDays=1
        )
        self.template.add_resource(log_group)

    def gen_execution_role(self):
        # IAM role that allows ECS to pull image from ECR
        # and write Cloudwatch logs.
        role_name = "conducto-demo-execution-role"
        self.execution_role = iam.Role(
            "ExecutionRole",
            RoleName=role_name,
            AssumeRolePolicyDocument=PolicyDocument(
                Version=self.IAM_POLICY_DOCUMENT_VERSION,
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[Action("sts", "AssumeRole")],
                        Principal=Principal("Service", "ecs-tasks.amazonaws.com"),
                    )
                ],
            ),
            Policies=[
                iam.Policy(
                    PolicyName=role_name,
                    PolicyDocument=PolicyDocument(
                        Version=self.IAM_POLICY_DOCUMENT_VERSION,
                        Statement=[
                            Statement(
                                Effect=Allow,
                                Action=[
                                    Action("ecr", "GetAuthorizationToken"),
                                    Action("ecr", "BatchCheckLayerAvailability"),
                                    Action("ecr", "GetDownloadUrlForLayer"),
                                    Action("ecr", "BatchGetImage"),
                                    Action("logs", "CreateLogGroup"),
                                    Action("logs", "CreateLogStream"),
                                    Action("logs", "PutLogEvents"),
                                ],
                                Resource=["*"],
                            ),
                            Statement(
                                Effect=Allow,
                                Action=[Action("iam", "PassRole")],
                                Resource=["arn:aws:iam::*:role/*"],
                            ),
                        ],
                    ),
                )
            ],
        )
        self.template.add_resource(self.execution_role)

    def gen_task_role(self):
        # IAM role that gives ECS task (the actual code in the service)
        # permissions to interact with AWS resources. We are deploying a
        # dummy service that does not need real access, so these permissions
        # are empty.
        role_name = "conducto-demo-task-role"
        self.task_role = iam.Role(
            "TaskRole",
            RoleName=role_name,
            AssumeRolePolicyDocument=PolicyDocument(
                Version=self.IAM_POLICY_DOCUMENT_VERSION,
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[Action("sts", "AssumeRole")],
                        Principal=Principal("Service", "ecs-tasks.amazonaws.com"),
                    )
                ],
            ),
            Policies=[
                iam.Policy(
                    PolicyName=role_name,
                    PolicyDocument=PolicyDocument(
                        Version=self.IAM_POLICY_DOCUMENT_VERSION,
                        Statement=[
                            Statement(
                                Effect=Allow,
                                Action=[Action("iam", "PassRole")],
                                Resource=["arn:aws:iam::*:role/*"],
                            ),
                        ],
                    ),
                )
            ],
        )
        self.template.add_resource(self.task_role)

    def get_service_image(self):
        ecr = boto3.client("ecr")
        result = ecr.describe_repositories(repositoryNames=["conducto-demo"])
        ecr_uri = result["repositories"][0]["repositoryUri"]
        return f"{ecr_uri}:latest"

    def gen_task_definition(self):
        log_configuration = ecs.LogConfiguration(
            LogDriver="awslogs",
            Options={
                "awslogs-group": self.log_group_name,
                "awslogs-region": Ref("AWS::Region"),
                "awslogs-stream-prefix": self.service_name,
            },
        )

        container_definition = ecs.ContainerDefinition(
            Name=self.service_name,
            Image=self.get_service_image(),
            PortMappings=[ecs.PortMapping(ContainerPort=80, Protocol="tcp")],
            LogConfiguration=log_configuration,
            Essential=True,
        )

        self.task_definition = ecs.TaskDefinition(
            "TasDefinition",
            Family="conducto-demo-family",
            ExecutionRoleArn=Ref(self.execution_role),
            TaskRoleArn=Ref(self.task_role),
            NetworkMode="awsvpc",
            RequiresCompatibilities=["FARGATE"],
            Cpu=f"0.25 vCPU",
            Memory="0.5 GB",
            ContainerDefinitions=[container_definition],
        )
        self.template.add_resource(self.task_definition)

    def gen_target_group(self):
        self.target_group = elasticloadbalancingv2.TargetGroup(
            "TargetGroup",
            VpcId=self.import_value("vpc", "VPC"),
            Port="80",
            TargetGroupAttributes=[
                elasticloadbalancingv2.TargetGroupAttribute(
                    Key="deregistration_delay.timeout_seconds", Value="10"
                ),
            ],
            TargetType="ip",
            Protocol="HTTP",
            HealthCheckPath="/demo",
        )
        self.template.add_resource(self.target_group)

    def gen_listener_rule(self):
        self.listener_rule = elasticloadbalancingv2.ListenerRule(
            "ListenerRule",
            Actions=[
                elasticloadbalancingv2.Action(
                    Type="forward", TargetGroupArn=Ref(self.target_group)
                )
            ],
            Conditions=[
                elasticloadbalancingv2.Condition(
                    Field="path-pattern",
                    PathPatternConfig=elasticloadbalancingv2.PathPatternConfig(
                        Values=["/demo/*", "/demo"]
                    ),
                )
            ],
            ListenerArn=self.import_value("load-balancer", "LoadBalancerListenerHTTP"),
            Priority=10,
        )
        self.template.add_resource(self.listener_rule)

    def gen_service(self):
        load_balancer = ecs.LoadBalancer(
            ContainerName=self.service_name,
            ContainerPort=80,
            TargetGroupArn=Ref(self.target_group),
        )

        # We put this service in public subnets because for demo purposes,
        # we only created public subnets. In a real application, you would
        # almost certainly put this in a private subnet.
        network_configuration = ecs.NetworkConfiguration(
            AwsvpcConfiguration=ecs.AwsvpcConfiguration(
                AssignPublicIp="ENABLED",
                Subnets=[
                    self.import_value("vpc", "PublicSubnet0"),
                    self.import_value("vpc", "PublicSubnet1"),
                ],
                SecurityGroups=[
                    self.import_value("load-balancer", "WebAppMembershipSecurityGroup"),
                    self.import_value("load-balancer", "WebAppSecurityGroup"),
                ],
            )
        )

        self.service = ecs.Service(
            "Service",
            ServiceName=self.service_name,
            Cluster=Ref(self.cluster),
            DeploymentConfiguration=ecs.DeploymentConfiguration(
                MinimumHealthyPercent=100, MaximumPercent=200
            ),
            DesiredCount=1,
            LaunchType="FARGATE",
            LoadBalancers=[load_balancer],
            NetworkConfiguration=network_configuration,
            SchedulingStrategy="REPLICA",
            TaskDefinition=Ref(self.task_definition),
        )
        self.template.add_resource(self.service)


if __name__ == "__main__":
    description = "Generate Cloudformation template for ECS service"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-o", action="store", required=True, dest="output_file")
    args = parser.parse_args()
    GenECSService(args.output_file)
