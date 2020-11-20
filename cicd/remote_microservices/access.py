"""
You'll need two (free) external accounts to continue.

    Heroku:     https://signup.heroku.com
    Redis Labs: https://redislabs.com/#signup-modal

Once logged in, collect details for your new accounts:

    From https://dashboard.heroku.com/account
     - HEROKU_API_KEY (it's at the bottom)

    Create a new db at https://app.redislabs.com, give it any name.
    Then copy these fields:
     - REDISLABS_DB_ENTRYPOINT
     - REDISLABS_DB_PASSWORD

Add the values above as secrets on your Conducto profile.

No Conducto account yet?  Modify the code below instead.

Once these values are stored, see README.md or pipeline.py.
"""
from pprint import pformat
from textwrap import indent
import conducto as co


# example data, don't use
# HEROKU_API_KEY = "e3281111-1111-1111-1111-b4631111b2fe"
# REDISLABS_DB_ENTRYPOINT = "redis-17350.c91.us-east-1-3.ec2.cloud.redislabs.com:17350"
# REDISLABS_DB_PASSWORD = "MS9nyx9GuTAAJ8aCuK34lpRxRHEzfnh5"

# If you don't have a conducto account, hard code your values below
HEROKU_API_KEY = None
REDISLABS_DB_ENTRYPOINT = None
REDISLABS_DB_PASSWORD = None


def env(tag: str, and_print=True) -> dict:
    """
    Initializes environment variables that provide external access

    Returns something like:
    {
      "HEROKU_API_KEY": "e3281111-1111-1111-1111-b4631111b2fe",
      "REDIS_HOST": "redis-17350.c91.us-east-1-3.ec2.cloud.redislabs.com",
      "REDIS_PORT": "17350",
      "REDIS_PASSWORD": "MS9nyx9GuTAAJ8aCuK34lpRxRHEzfnh5",
      "REDIS_KEY": "MS9nyx9GuTAAJ8aCuK34lpRxRHEzfnh5",
      "NAME": "co-12-bestuser-prod",
      "CONDUCTO_USER": "bestuser",
      "CONDUCTO_USER_FAKE_EMAIL": "bestuser+fakeaddr@bestorg.conducto"
    }
    """

    env = {}
    for key, value in {
        "HEROKU_API_KEY": HEROKU_API_KEY,
        "REDISLABS_DB_ENTRYPOINT": REDISLABS_DB_ENTRYPOINT,
        "REDISLABS_DB_PASSWORD": REDISLABS_DB_PASSWORD,
    }.items():
        env.update(_to_env([key, value]))

    env["TAG"] = tag
    env["NAME"] = profile.my_env(tag)

    # for git config
    env["CONDUCTO_USER"] = profile.name
    env["CONDUCTO_USER_FAKE_EMAIL"] = profile.email

    if and_print:
        print(f"{tag} env:")
        print(indent(pformat(env), 4 * " "))

    return env


def _to_env(kvp: list) -> dict:
    """Translate from external secretes into environment vars"""

    # get value from user secrets
    def fetch(key, value):
        if not value:
            return co.api.Secrets().get_user_secrets()[key]
        else:
            return value

    key = kvp[0]
    value = fetch(key, kvp[1])

    env = {}

    # separate parts
    if key == "REDISLABS_DB_ENTRYPOINT":
        host, port = value.split(":")
        env["REDIS_HOST"] = host
        env["REDIS_PORT"] = port

    # simplify name
    elif key == "REDISLABS_DB_PASSWORD":
        env["REDIS_PASSWORD"] = fetch(key, value)

    # leave alone
    else:
        env[key] = fetch(key, value)

    return env


class UserStrings:
    def clean(dirty):
        return "".join(c for c in dirty if c.isalnum()).lower()

    def __init__(self):
        dir_api = co.api.Dir()
        user = dir_api.user()
        org = dir_api.org_by_user()

        self.name = UserStrings.clean(user["name"])
        org_id = user["org_id"]
        org_name = UserStrings.clean(org["name"])
        self.env_template = "-".join(["co", str(org_id), self.name, "{}"])
        self.email = self.name + "+fakeaddr@" + org_name + ".conducto"

    def my_env(self, tag: str) -> str:
        """
        A unique string to differentiate this app from others.

        tag: differentiates environments, like "test" vs "prod"

        Returns things like: "co-12-pocahontas-test"
        """

        return self.env_template.format(tag)


# get user details from conducto
profile = UserStrings()
