import conducto as co
import click
import sys
from copy import deepcopy

import co_env

CRC = co.ContainerReuseContext

secret_keys = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
]


# By Hand:
# 1. create an IAM group called "ConductoUsers" with AmazonS3FullAccess policy
# 2. create an IAM user with programmatic access called "cicd" in that group
# 3. install the aws cli (https://aws.amazon.com/cli/)
# 4. run `aws configure` and supply secrets for "cicd"
# 5. run this pipeline (which will pluck those secrets from ~/.aws)


def tag(org_id, user_name=None):
    if user_name:
        return f"{org_id}-{user_name}"
    else:
        return str(org_id)


def terraform(tag):

    with co.Serial(
        image=co.Image(dockerfile="./terraform/Dockerfile"),
        container_reuse_context=CRC.NEW,
    ) as node:

        # populate terraform vars from env
        # use bash variables for secrets so they aren't displayed in pipeline command
        tfvars = {k.lower: "${}".format(k) for k in secret_keys}
        tfvars["tag"] = tag

        # write it to terraform.tvfars
        tfvars_echo = "\n".join(["{} = {}".format(k, v) for k, v in tfvars.items()])
        cmd = f"""
              echo "{tfvars_echo}" \\
                  > terraform.tfvars
              """

        co.Exec(cmd, env=env_vars, name="stage parameters")
        co.Exec(f"terraform plan", name="announce plan")

    return node


def ensure_prod_infra() -> co.Serial:
    return terraform(tag(org_id))


def ensure_dev_infra() -> co.Serial:
    return terraform(tag(co_env.org_id, user_name=co_env.user_name))


env_vars = None
if __name__ == "__main__":

    co.Image.share_directory("y_js", ".")

    # update conducto user's secret store
    co_env.stash_secrets(secret_keys)

    # make secrets available to the pipeline
    env_vars = co_env.secrets

    co.main()
