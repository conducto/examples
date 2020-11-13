"""
### Simple AWS CI/CD Pipeline

This is a CI/CD pipeline that deploys a simple flask microservice
into AWS Elastic Container Service behind a load balancer, tests
it, and then cleans up all AWS resources.

You must have an AWS account and specify the following as secrets
in the Conducto app:
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_DEFAULT_REGION

Note that this pipeline allocates AWS resources that may incur a
charge while running. Do not forget to unskip and run the "Cleanup"
node when you are done to delete these AWS resources.
"""

import conducto as co

########################################################################
# Pipeline Defintion
########################################################################


def main() -> co.Serial:
    img = co.Image(dockerfile="./Dockerfile", reqs_docker=True)
    with co.Serial(image=img, doc=__doc__) as root:
        with co.Parallel(name="Init", doc=INIT_DOC) as init:
            init["Deploy Infra"] = deploy_infra()
            init["Deploy Image"] = deploy_image()
            init["Lint"] = co.Exec("black --check .")
            init["Unit Test"] = co.Exec("python service/test.py --verbose")
        root["Deploy Service"] = deploy_service()
        root["Integration Test"] = co.Exec(INTEGRATION_CMD, doc=INTEGRATION_DOC)
        root["Cleanup"] = cleanup()
    return root


def deploy_infra() -> co.Serial:
    vpc_cmd = DEPLOY_STACK_CMD.format(stack="vpc")
    elb_cmd = DEPLOY_STACK_CMD.format(stack="elb")
    with co.Serial() as output:
        co.Exec(vpc_cmd, name="VPC")
        co.Exec(elb_cmd, name="ELB")
    return output


def deploy_image() -> co.Serial:
    with co.Serial() as output:
        co.Exec(CREATE_REPO_CMD, name="Create Repo")
        co.Exec(BUILD_AND_PUSH_CMD, name="Build and Push", requires_docker=True)
    return output


def deploy_service() -> co.Exec:
    service_cmd = DEPLOY_STACK_CMD.format(stack="service")
    return co.Exec(service_cmd)


def cleanup() -> co.Serial:
    delete_service_cmd = DELETE_STACK_CMD.format(stack="service")
    delete_elb_cmd = DELETE_STACK_CMD.format(stack="elb")
    delete_vpc_cmd = DELETE_STACK_CMD.format(stack="vpc")
    with co.Serial(skip=True, doc=CLEANUP_DOC) as output:
        co.Exec(delete_service_cmd, name="Service")
        co.Exec(delete_elb_cmd, name="ELB")
        co.Exec(delete_vpc_cmd, name="VPC")
        co.Exec(DELETE_REPO_CMD, name="Repo")
    return output


########################################################################
# Commands
########################################################################

DEPLOY_STACK_CMD = """
set -ex
cd cloudformation

# Use Troposphere to generate the CloudFormation template
python {stack}.py -o template.yml
cat template.yml

# Validate and deploy it
aws cloudformation validate-template --template-body file://template.yml
aws cloudformation deploy --template-file template.yml \\
  --stack-name conducto-demo-{stack} --capabilities CAPABILITY_NAMED_IAM
"""

CREATE_REPO_CMD = "aws ecr create-repository --repository-name conducto-demo || true"

GET_REPO_CMD = """
aws ecr describe-repositories --repository-names conducto-demo | \\
  grep repositoryUri | cut -d: -f2 | tr -d '", ' | cut -d/ -f1
"""

BUILD_AND_PUSH_CMD = f"""
set -ex
cd service
ECR_URI=$({GET_REPO_CMD})
docker build -t $ECR_URI/conducto-demo:latest .
aws ecr get-login-password --region $AWS_DEFAULT_REGION | \\
  docker login --username AWS --password-stdin $ECR_URI
docker push $ECR_URI/conducto-demo:latest
"""

GET_DNS_NAME_CMD = """
aws cloudformation describe-stacks --stack-name conducto-demo-elb | \\
  grep -A1 '"DNSName"' | tail -1 | cut -d: -f2 | tr -d '", '
"""

INTEGRATION_CMD = f"""
set -e
export URL=http://$({GET_DNS_NAME_CMD})
echo "Testing URL=$URL"

# Call '/', which outputs a Hello World message
OUTPUT=$(curl -s $URL/demo)
echo "GET /demo -> $OUTPUT"
test "$OUTPUT" == "Hello, Conducto!"

# Post data to /demo/user, which gets saved
OUTPUT=$(
  curl -s -X POST -H "Content-Type: application/json" \\
  -d '{{"key": "age", "value": "42"}}' $URL/demo/user/BobLoblaw
)
echo "POST /user/BobLoblaw -> $OUTPUT"
test "$OUTPUT" == '{{"user": "BobLoblaw", "data": {{"age": "42"}}}}'

# Request the same data from /demo/user
OUTPUT=$(curl -s $URL/demo/user/BobLoblaw)
echo "GET /user/BobLoblaw -> $OUTPUT"
test "$OUTPUT" == '{{"user": "BobLoblaw", "data": {{"age": "42"}}}}'

# Test that the 'hacker' user is disallowed
OUTPUT=$(curl -s $URL/demo/user/hacker)
echo "GET /user/hacker -> $OUTPUT"
test "$OUTPUT" == '{{"error": "Unauthorized"}}'
"""

DELETE_STACK_CMD = """
set -e
STACK=conducto-demo-{stack}
echo "Deleting stack $STACK"
aws cloudformation delete-stack --stack-name $STACK
while OUTPUT=$(aws cloudformation describe-stacks --stack-name $STACK | grep StackStatus); do
    echo $(date +"%T") $OUTPUT
    sleep 5
done
echo "Successfully deleted stack $STACK"
"""

DELETE_REPO_CMD = """
aws ecr delete-repository --repository-name conducto-demo --force || true
"""


########################################################################
# Docs
########################################################################

INIT_DOC = """
Run the initialization steps in parallel:
* Deploy the AWS infrastructure
* Build the docker image for the service
* Run a linter
* Unit test the service
"""

INTEGRATION_DOC = """
Now that the service is deployed, make some http requests to confirm
that it is working.
"""

CLEANUP_DOC = """
Unskip this node when you are ready to cleanup all of the AWS resources
created by this pipeline. It deletes the cloudformation stacks used to
deploy the service, ELB, and and VPC, then uses the AWS CLI to delete
the ECR repo. Note that AWS requires that the cloudformation stacks be
deleted in serial, due to dependencies between the stacks.
"""


if __name__ == "__main__":
    co.main(default=main)
