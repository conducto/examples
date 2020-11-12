import argparse
from troposphere import Template, Ref, GetAtt, ImportValue, Output, Export
from troposphere import ec2, elasticloadbalancingv2


class GenLoadBalancer(object):
    def __init__(self, output_file):
        self.init_template()
        self.gen_web_app_membership_security_group()
        self.gen_load_balancer_security_group()
        self.gen_web_app_security_group()
        self.gen_default_target_group()
        self.gen_load_balancer()
        self.gen_load_balancer_listener()
        self.write_template(output_file)

    def init_template(self):
        self.template = Template(Description="load balancer resources")

    def write_template(self, output_file):
        with open(output_file, "w") as f:
            f.write(self.template.to_yaml())

    def import_value(self, stack_name, value_name):
        return ImportValue(f"conducto-demo-{stack_name}-{value_name}")

    def export_value(self, value, value_name):
        export_name = f"conducto-demo-load-balancer-{value_name}"
        return self.template.add_output(
            Output(value_name, Value=value, Export=Export(export_name))
        )

    def get_security_group_rule_anybody(self, port, desc):
        return ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=str(port),
            ToPort=str(port),
            CidrIp="0.0.0.0/0",
            Description=desc,
        )

    def get_security_group_rule_source_group(self, port, source, desc):
        return ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=str(port),
            ToPort=str(port),
            SourceSecurityGroupId=Ref(source),
            Description=desc,
        )

    def gen_web_app_membership_security_group(self):
        self.web_app_membership_security_group = ec2.SecurityGroup(
            "WebAppMembershipSecurityGroup",
            GroupDescription="Security group to identify web apps, no rules",
            SecurityGroupIngress=[],
            SecurityGroupEgress=[],
            VpcId=self.import_value("vpc", "VPC"),
        )
        self.template.add_resource(self.web_app_membership_security_group)

        value = Ref(self.web_app_membership_security_group)
        self.export_value(value, "WebAppMembershipSecurityGroup")

    def gen_load_balancer_security_group(self):
        ingress_rules = [
            self.get_security_group_rule_anybody(80, "HTTP from anybody"),
            self.get_security_group_rule_anybody(443, "HTTPS from anybody"),
        ]

        egress_rules = [
            self.get_security_group_rule_source_group(
                80, self.web_app_membership_security_group, "HTTP to web apps in VPC",
            )
        ]

        self.load_balancer_security_group = ec2.SecurityGroup(
            "LoadBalancerSecurityGroup",
            GroupDescription="Load balancer security group",
            SecurityGroupIngress=ingress_rules,
            SecurityGroupEgress=egress_rules,
            VpcId=self.import_value("vpc", "VPC"),
        )
        self.template.add_resource(self.load_balancer_security_group)

    def gen_web_app_security_group(self):
        ingress_rules = [
            self.get_security_group_rule_source_group(
                80, self.load_balancer_security_group, "HTTP from load balancer",
            )
        ]

        egress_rules = [
            self.get_security_group_rule_anybody(80, "HTTP from anybody"),
            self.get_security_group_rule_anybody(443, "HTTPS from anybody"),
        ]

        self.web_app_security_group = ec2.SecurityGroup(
            "WebAppSecurityGroup",
            GroupDescription="Web app security group",
            SecurityGroupIngress=ingress_rules,
            SecurityGroupEgress=egress_rules,
            VpcId=self.import_value("vpc", "VPC"),
        )
        self.template.add_resource(self.web_app_security_group)

        value = Ref(self.web_app_security_group)
        self.export_value(value, "WebAppSecurityGroup")

    def gen_default_target_group(self):
        self.default_target_group = elasticloadbalancingv2.TargetGroup(
            "DefaultTargetGroup",
            VpcId=self.import_value("vpc", "VPC"),
            Port="80",
            TargetType="ip",
            Protocol="HTTP",
        )
        self.template.add_resource(self.default_target_group)

    def gen_load_balancer(self):
        self.load_balancer = elasticloadbalancingv2.LoadBalancer(
            "LoadBalancer",
            SecurityGroups=[Ref(self.load_balancer_security_group)],
            Subnets=[
                self.import_value("vpc", "PublicSubnet0"),
                self.import_value("vpc", "PublicSubnet1"),
            ],
            Scheme="internet-facing",
        )
        self.template.add_resource(self.load_balancer)

        value = GetAtt(self.load_balancer, "DNSName")
        self.export_value(value, "DNSName")

    def gen_load_balancer_listener(self):
        # This forwards incoming traffic on port 80 (HTTP) to the default
        # target group. If you were doing this for real, it would be better
        # to redirect incoming traffic on port 80 to port 443 (HTTPS), and
        # add a second listener that forwards traffic from port 443 to the
        # default target group.
        self.load_balancer_listener_http = elasticloadbalancingv2.Listener(
            "LoadBalancerListenerHTTP",
            LoadBalancerArn=Ref(self.load_balancer),
            Port="80",
            Protocol="HTTP",
            DefaultActions=[
                elasticloadbalancingv2.Action(
                    Type="forward", TargetGroupArn=Ref(self.default_target_group)
                )
            ],
        )
        self.template.add_resource(self.load_balancer_listener_http)

        value = Ref(self.load_balancer_listener_http)
        self.export_value(value, "LoadBalancerListenerHTTP")


if __name__ == "__main__":
    description = "Generate Cloudformation template for load balancer"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-o", action="store", required=True, dest="output_file")
    args = parser.parse_args()
    GenLoadBalancer(args.output_file)
