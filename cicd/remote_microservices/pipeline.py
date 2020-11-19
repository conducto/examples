"""
### Two Remote Microservices
#### (Flask in Heroku, Redis in RedisLabs)

This pipeline definition deploys an app to a test environment.  Then it tests
it there.  If all goes well, it deploys to prod.

It assumes that the redis service is already up (suppose that another
team is responsible for keeping redis up).

The flask app is our responsibility, so this pipeline tests and deploys it.

You'll need some external account to make it work.  To configure access
to the necessary infrastructure services, see access.py.
"""

import conducto as co

# see access.py to set up credentials
import access

# we'll need these tools
infractl_image = "finalgene/heroku-cli"
test_image = co.Image(reqs_packages=["redis", "curl"])

repo = "https://github.com/conducto/examples"
prod_branch = "main"


def main(src_image, test_env, prod_env=None) -> co.Serial:
    """
    Test the code, deploy if appropriate.
    """

    with co.Serial(doc=__doc__, image=src_image, env=test_env.copy()) as root:

        # can we autenticate?  If not, fail early.
        with co.Parallel(name="access check"):

            access.ensure_ssh(name="ensure ssh")
            co.Exec(TEST_HEROKU_CMD, image=infractl_image, name="Heroku")
            co.Exec(TEST_REDIS_CMD, image=test_image, name="RedisLabs")

        # test the code in a test env
        with co.Serial(name="test"):

            deploy(src_image, test_env, name="deploy")
            co.Exec(INTEGRATION_TEST_CMD, name="test")

        # if CI + CD, deploy it to a prod env
        if prod_env:
            deploy(src_image, prod_env, name="deploy")

        # Unskip a child of teardown to remove either env
        with co.Serial(skip=True, name="teardown"):
            teardown(test_env, name=test_env["NAME"])
            if prod_env:
                teardown(prod_env, name=prod_env["NAME"])

    return root


def deploy(src_image: co.Image, env: dict, **kwargs) -> co.Serial:
    """
    Put the code in an environment.
    """

    with co.Serial(env=env.copy(), **kwargs) as node:

        # deploy the code
        with co.Serial(name=env["NAME"]) as deploy:

            deploy["create"] = co.Exec(CREATE_APP_CMD)

            push_cmd = PUSH_CODE_CMD.format(src=src_image.path_to_code, repo=repo)
            deploy["push"] = co.Exec(push_cmd)

        # fail if we can't see the service
        node["sanity check"] = co.Exec(TEST_FLASK_CMD, image=test_image)

    return node


def teardown(env: dict, **kwargs) -> co.Parallel:
    """
    Un-deploy an environment.
    """

    with co.Parallel(env=env.copy(), **kwargs) as down:
        down["clear data"] = co.Exec(CLEAR_DATA_CMD, image=test_image)
        down["stop flask"] = co.Exec(STOP_FLASK_CMD, image=infractl_image)

    return down


########################################################################
# Commands
########################################################################

TEST_REDIS_CMD = """
set -ex
redis-cli -h "$REDIS_HOST" \\
          -p "$REDIS_PORT" \\
          -a "$REDIS_PASSWORD" ping | grep PONG
"""

TEST_HEROKU_CMD = """
set -ex
echo $HEROKU_API_KEY
heroku auth:whoami
"""


CREATE_APP_CMD = """
set -ex
if heroku apps | grep "$NAME" > /dev/null
then
    echo "found $NAME"
else
    heroku apps:create "$NAME"
fi
"""

PUSH_CODE_CMD = """
set -ex

# prepare creds for git push
KEYFILE = /root/.ssh/id_rsa
echo "$HEROKU_SSH_PRIVKEY" > "$KEYFILE"
chmod 700 "$KEYFILE"

# grab outer repo details, if available
REV=$(git rev-parse HEAD) 2>/dev/null || x=NO_SHA

# prepare inner repo for push
cd {src}
git init
git config --local user.email "$CONDUCTO_USER_FAKE_EMAIL"
git config --local user.name "$CONDUCTO_USERNAME"
git config --local url.ssh://git@heroku.com/.insteadOf https://git.heroku.com/
heroku git:remote -a "$NAME"

# push code to heroku
git add -A
git commit -m "{repo}@$REV"
git push heroku master
"""


TEST_FLASK_CMD = """
set -ex
FLASK_IP=$(conducto-data-pipeline gets /flask/ip)
curl $FLASK_IP:5000
"""

INTEGRATION_TEST_CMD = """
set -ex

# two requests for flask
FLASK_IP=$(conducto-data-pipeline gets /flask/ip)
curl -s $FLASK_IP:5000 | egrep -o '[0-9]+' > first
curl -s $FLASK_IP:5000 | egrep -o '[0-9]+' > second

# did they increment?
let FIRST_PLUS_ONE="$(cat first)+1"
cat second | grep $FIRST_PLUS_ONE
"""

CLEAR_DATA_CMD = """
set -ex
redis-cli -h "$REDIS_IP" \\
          -p "$REDIS_PORT" \\
          -a "$REDIS_PASSWORD" ping | grep PONG
"""

STOP_FLASK_CMD = "docker stop my_flask"

########################################################################
# Entrypoints
########################################################################

# .conducto.cfg determines which of these functions gets called in
# response to source control activity

# if conducto is installed locally, you can also call them with a command:

test_env = access.env("test")
test_env_name = test_env["NAME"]


def testlocal() -> co.Serial:
    """
    Triggered by a human
    """

    src_img = get_src_img(copy_dir=".")
    src_img.path_to_code = "."

    print(f"Testing code from local filesystem in {test_env_name}")

    return main(src_img, test_env)


def pr(branch: str) -> co.Serial:
    """
    Triggered by a PR
    """

    src_img = get_src_img(copy_repo=True)
    src_img.path_to_code = "./cicd/remote_microservices"

    print(f"Testing branch indicated by PR in {test_env_name}")

    return main(src_img, test_env)


def merge() -> co.Serial:
    """
    Triggered from a merge to "main"
    """

    src_img = get_src_img(copy_url=repo, copy_branch=prod_branch)
    src_img.path_to_code = "./cicd/remote_microservices"

    print(f"Testing branch: {prod_branch} in  {test_env_name}")

    prod_env = access.env("prod")
    prod_env_name = prod_env["Name"]

    print(f"...if it passes, will deploy to {prod_env_name}")

    return main(src_img, test_env, prod_env=prod_env)


# Helper for injecting code into the deploy image
def get_src_img(**kwargs):
    return co.Image(image=infractl_image, reqs_packages=["git"], **kwargs)


if __name__ == "__main__":

    # If you're in a sandbox, uncomment only one of these or install
    # condcuto for local control

    # test local code
    co.main(default=testlocal)

    # test code from git branch
    # co.main(argv=["pr", "my_feature"])

    # test code from main branch
    # co.main(default=merge)
