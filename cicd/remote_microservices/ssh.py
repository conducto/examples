import conducto as co

key_key = "HEROKU_SSH_PRIVKEY_BASE64"
key_file = "/root/.ssh/id_ed25519"


def prep(**kwargs):
    """
    Ensures that the user secret: HEROKU_SSH_PRIVKEY_BASE64 is registered with
    heroku and works to authenticate with them.
    """

    with co.Serial(**kwargs) as node:

        gen = co.Exec(ssh_keygen)
        node["gen key if missing"] = gen
        # more...

        co.Exec(REGISTER_KEY_CMD, name="register key")
        co.Exec(TEST_KEY_CMD, name="test key")

    return node


def ssh_keygen():

    from sh import ssh_keygen, bash

    secrets_api = co.api.Secrets()
    user_secrets = secrets_api.get_user_secrets()

    if key_key not in user_secrets:
        print(f"{key_key} not found, generating a new key")
        ssh_keygen(["-t", "ed25519", "-N", "", "-f", key_file], _tee=True)
        base64_key = str(bash(["-c", f"cat {key_file} | base64"]))

        with open(key_file, "r") as f:
            secrets_api.put_user_secrets({key_key: base64_key})

        print(f"{key_key} added to user secrets")

    else:
        print(f"{key_key} found")


########################################################################
# Commands
########################################################################

REGISTER_KEY_CMD = f"""
set -e

# restore key if not already in place
if [ ! -f {key_file} ]
then
    # restore key from user secrets
    mkdir -p $(dirname {key_file})
    echo ${key_key} | base64 -d > {key_file}
    chmod 600 {key_file}
fi

# prepare public key
set -x
ssh-keygen -y -f {key_file} > pubkey

# register it
echo "Adding public key:"
cat pubkey
heroku keys:add pubkey
"""

ssh_middle = f"-i {key_file} -o StrictHostKeyChecking=no -T git@heroku.com"
TEST_KEY_CMD = f"""
set -ex

# test ssh key
ssh {ssh_middle} 2>&1 | grep -v 'Permission denied'
ssh -v {ssh_middle} 2>&1  | grep 'Authentication succeeded'
"""
