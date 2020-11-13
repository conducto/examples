# Troposphere? CloudFormation?
AWS CloudFormation templates are written in JSON or YAML. Conducto prefers code to config, so this example uses the excellent [Troposphere](https://github.com/cloudtools/troposphere) package to generate CloudFormation templates. Conducto's internal CI/CD is built upon Troposphere.

We are also big fans of [Pulumi](https://www.pulumi.com) and the [AWS CDK](https://aws.amazon.com/cdk/) for scripting AWS infrastructure using code. 