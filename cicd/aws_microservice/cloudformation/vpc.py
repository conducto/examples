import argparse
from troposphere import Template, Ref, Output, Export, Select, GetAZs
from troposphere import ec2


class GenVPC(object):
    def __init__(self, output_file):
        self.init_template()
        self.gen_vpc()
        self.gen_internet_gateway()
        self.gen_internet_gateway_attachment()
        self.gen_public_route_table()
        self.gen_public_route()
        self.gen_network_acl()
        self.gen_public_subnet_az(az_index=0, cidr_block="10.0.0.0/24")
        self.gen_public_subnet_az(az_index=1, cidr_block="10.0.1.0/24")
        self.write_template(output_file)

    def init_template(self):
        self.template = Template(Description="vpc, gateway, route, subnet")

    def write_template(self, output_file):
        with open(output_file, "w") as f:
            f.write(self.template.to_yaml())

    def export_value(self, value, value_name):
        export_name = f"conducto-demo-vpc-{value_name}"
        return self.template.add_output(
            Output(value_name, Value=value, Export=Export(export_name))
        )

    def gen_vpc(self):
        self.vpc = ec2.VPC(
            "VPC",
            CidrBlock="10.0.0.0/16",
            EnableDnsSupport=True,
            EnableDnsHostnames=True,
        )
        self.template.add_resource(self.vpc)
        self.export_value(Ref(self.vpc), "VPC")

    def gen_internet_gateway(self):
        self.internet_gateway = ec2.InternetGateway("InternetGateway")
        self.template.add_resource(self.internet_gateway)

    def gen_internet_gateway_attachment(self):
        self.internet_gateway_attachment = ec2.VPCGatewayAttachment(
            "InternetGatewayAttachment",
            VpcId=Ref(self.vpc),
            InternetGatewayId=Ref(self.internet_gateway),
        )
        self.template.add_resource(self.internet_gateway_attachment)

    def gen_public_route_table(self):
        self.public_route_table = ec2.RouteTable(
            "PublicRouteTable", VpcId=Ref(self.vpc)
        )
        self.template.add_resource(self.public_route_table)

    def gen_public_route(self):
        self.public_route = ec2.Route(
            "PublicRoute",
            RouteTableId=Ref(self.public_route_table),
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=Ref(self.internet_gateway),
            DependsOn=self.internet_gateway_attachment,
        )
        self.template.add_resource(self.public_route)

    def gen_network_acl(self):
        self.network_acl = ec2.NetworkAcl("NetworkAcl", VpcId=Ref(self.vpc))
        self.template.add_resource(self.network_acl)

        # Allow all inbound and outbound traffic for http, https, and
        # ephemeral ports for load balancers. Deny all other traffic.
        rule_number = 100
        port_ranges = [(80, 80), (443, 443), (1024, 65535)]
        for p in port_ranges:
            for egress in [False, True]:
                entry_type = "Egress" if egress else "Ingress"
                name = f"NetworkAcl{entry_type}{p[0]}"
                network_acl_entry = ec2.NetworkAclEntry(
                    name,
                    NetworkAclId=Ref(self.network_acl),
                    CidrBlock="0.0.0.0/0",
                    Egress=egress,
                    PortRange=ec2.PortRange(From=p[0], To=p[1]),
                    Protocol=6,  # TCP
                    RuleAction="allow",
                    RuleNumber=rule_number,
                )
                self.template.add_resource(network_acl_entry)
            rule_number += 10

    def gen_public_subnet_az(self, az_index, cidr_block):
        name = f"PublicSubnet{az_index}"
        subnet = ec2.Subnet(
            name,
            VpcId=Ref(self.vpc),
            CidrBlock=cidr_block,
            AvailabilityZone=Select(str(az_index), GetAZs(Ref("AWS::Region"))),
        )
        self.template.add_resource(subnet)
        self.export_value(Ref(subnet), name)

        route_table_association = ec2.SubnetRouteTableAssociation(
            f"{name}RouteTableAssociation",
            SubnetId=Ref(subnet),
            RouteTableId=Ref(self.public_route_table),
        )
        self.template.add_resource(route_table_association)

        network_acl_association = ec2.SubnetNetworkAclAssociation(
            f"{name}NetworkAclAssociation",
            SubnetId=Ref(subnet),
            NetworkAclId=Ref(self.network_acl),
        )
        self.template.add_resource(network_acl_association)


if __name__ == "__main__":
    description = "Generate Cloudformation template for VPC resources"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-o", action="store", required=True, dest="output_file")
    args = parser.parse_args()
    GenVPC(args.output_file)
