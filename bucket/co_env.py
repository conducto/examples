import os
import configparser
import click
import sys
from copy import deepcopy
import conducto as co

secrets = None
user_name = None
org_id = None

def stash_secrets(keys):
    """
    Read from aws cli env
    Write to conducto user secret store
    Warn user before making changes
    Populate secrets, user_name, and org_id
    """
    
    global secrets, user_name, org_id
    
    # get preexisting conducto user secrets
    auth = co.api.Auth()
    token = auth.get_token_from_shell()
    secrets_api = co.api.Secrets()
    existing = secrets_api.get_user_secrets()
    
    # prepare to update them with aws secrets from env
    add = set()
    update = set()
    inbound = get_aws_secrets()
    for required in keys:
        try:
            if inbound[required] != existing[required]:
                update.add(required)
        except KeyError:
            add.add(required)
            
    # update conducto secrets if necessary
    if add.union(update):
        print("add secrets:", add or "{}")
        print("update secrets:", update or "{}")
        if not click.confirm("continue?", default=True):
            sys.exit(1)
        outbound = deepcopy(existing)
        outbound.update(inbound)
        secrets_api.put_user_secrets(outbound, token)
        secrets = outbound
        print("done")
    else:
        secrets = inbound
        
    # get unique strings for user
    user = co.api.Dir().user()
    user_name = user['name']
    org_id = user['org_id']
    
    
def get_aws_secrets():
    env = {}
    cfg_dir = os.path.expanduser("~/.aws")
    if all(
        os.path.exists(os.path.join(cfg_dir, fname))
        for fname in ["config", "credentials"]
    ):
        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(cfg_dir, "credentials"))
        env["AWS_ACCESS_KEY_ID"] = cfg.get("default", "aws_access_key_id")
        env["AWS_SECRET_ACCESS_KEY"] = cfg.get("default", "aws_secret_access_key")
        cfg.read(os.path.join(cfg_dir, "config"))
        env["AWS_DEFAULT_REGION"] = cfg.get("default", "region")
    else:
        try:
            env["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
            env["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
            env["AWS_DEFAULT_REGION"] = os.environ.get(
                "AWS_DEFAULT_REGION", "us-east-2"
            )
        except KeyError:
            raise Exception(
                f"Must supply AWS credentials, either through "
                f"environment variables or ~/.aws/credentials."
            )
    return env