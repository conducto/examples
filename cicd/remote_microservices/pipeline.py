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
import ssh

CRC = co.ContainerReuseContext

# we'll need these tools
infractl_image = "finalgene/heroku-cli"
test_image = co.Image(reqs_packages=["redis", "curl"])

# production tracks this branch
repo = "https://github.com/conducto/examples"
prod_branch = "main"


def main(src_image, test_env, prod_env=None) -> co.Serial:
    """
    Test the code, deploy if appropriate.
    """

    with co.Serial(doc=__doc__, image=src_image, env=test_env.copy()) as root:

        # can we autenticate?  If not, fail early.
        with co.Parallel(name="access check"):

            co.Exec(TEST_HEROKU, image=infractl_image, name="Heroku  API")
            co.Exec(TEST_REDIS, image=test_image, name="RedisLabs")

        # test the code in a test env
        with co.Serial(name="test"):

            deploy(src_image, test_env, name="deploy " + test_env["NAME"])
            co.Exec(INTEGRATION_TEST, name="integration test", image=test_image)

        # if CI + CD, deploy it to a prod env
        if prod_env:
            deploy(src_image, prod_env, name="deploy " + prod_env["NAME"])

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

        with co.Serial(name="env up"):

            co.Exec(CREATE_APP, name="create app")
            co.Exec(STOP_APP, name="stop if not already")
            co.Exec(CONFIGURE_APP, name="configure app")

            with co.Serial(container_reuse_context=CRC.NEW, name="move bits"):

                # The key can't be recalled if it was created by this
                # pipeline.  My workaround is to leave it in the
                # container.  This means that this has to happen at
                # every deploy, rather that up in access_check where it
                # belongs
                ssh.prep(name="prepare ssh")

                push_cmd = PUSH_CODE.format(src=src_image.path_to_code, repo=repo)
                co.Exec(push_cmd, name="push code")

            co.Exec(START_APP, name="start app")

        # fail if obvious things are wrong
        with co.Parallel(name="sanity check"):
            co.Exec(PEEK_LOGS, name="peek at logs")
            co.Exec(TEST_FLASK, image=test_image, name="check alive")

    return node


def teardown(env: dict, **kwargs) -> co.Parallel:
    """
    Un-deploy an environment.
    """

    with co.Parallel(env=env.copy(), **kwargs) as down:
        co.Exec(CLEAR_DATA, image=test_image, name="clear data")
        co.Exec(STOP_APP, name="stop")
        co.Exec(DESTROY_APP, name="destroy")

    return down


########################################################################
# Commands
########################################################################

TEST_REDIS = """
set -eux
redis-cli -h "$REDIS_HOST" \\
          -p "$REDIS_PORT" \\
          -a "$REDIS_PASSWORD" ping | grep PONG
"""

TEST_HEROKU = """
set -eux
echo $HEROKU_API_KEY
heroku auth:whoami
"""


CREATE_APP = """
set -eux

if heroku apps | grep "$NAME" > /dev/null
then
    echo "found $NAME"
else
    heroku apps:create "$NAME"
fi
"""

PUSH_CODE = """
set -euxo pipefail

SRC_DIR=$(readlink -f {src})

# grab outer repo details, if available
REV=$(git rev-parse HEAD) 2>/dev/null || x=NO_SHA

# prepare inner repo for push
cd $SRC_DIR
git init
git config --global user.email "$CONDUCTO_USER_FAKE_EMAIL"
git config --global user.name "$CONDUCTO_USER"
git config --global url.ssh://git@heroku.com/.insteadOf https://git.heroku.com/
heroku git:remote -a "$NAME"

# push code to heroku
git add -A
git commit -m "{repo}@$REV"
git push -f heroku master 2>&1 \\
    | tee /dev/fd/2 \\
    | tee remote_logs \\
    | grep 'Verifying deploy... done'

# if successful, stash url
cat remote_logs \\
    | grep 'herokuapp.com' \\
    | egrep -o 'https://[^ ]*' \\
    | tee >(conducto-data-pipeline puts "/$TAG/url")

"""

CONFIGURE_APP = """
set -eux
heroku config:set \\
    TAG=$TAG \\
    REDIS_HOST=$REDIS_HOST \\
    REDIS_PORT=$REDIS_PORT \\
    REDIS_PASSWORD=$REDIS_PASSWORD \\
    -a $NAME
"""

START_APP = """
set -eux
heroku ps:scale web=1 -a "$NAME"
"""

PEEK_LOGS = """
set -euxo pipefail
sleep 3

heroku logs -a "$NAME" \\
    | tail -n 30 \\
    | tee log_snippet 1>&2

grep -i 'starting gunicorn' log_snippet
grep -i 'listening' log_snippet
"""

TEST_FLASK = """
set -ex
FLASK_URL=$(conducto-data-pipeline gets /$TAG/url)
curl -vf $FLASK_URL
"""

INTEGRATION_TEST = """
set -ex

# two requests for flask
FLASK_URL=$(conducto-data-pipeline gets /$TAG/url)
curl -s $FLASK_URL | egrep -o '[0-9]+' > first
curl -s $FLASK_URL | egrep -o '[0-9]+' > second

# did they increment?
let FIRST_PLUS_ONE="$(cat first)+1"
cat second | grep $FIRST_PLUS_ONE
"""

CLEAR_DATA = """
set -ex
redis-cli -h "$REDIS_HOST" \\
          -p "$REDIS_PORT" \\
          -a "$REDIS_PASSWORD" del "$TAG"
"""

STOP_APP = """
set -eux
heroku ps:scale web=0 -a "$NAME" || true
"""

DESTROY_APP = """
set -eux
heroku apps:destroy -a "$NAME" --confirm="$NAME"
"""

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

    print(f"Testing code from local filesystem in remote env: {test_env_name}")

    return main(src_img, test_env)


def pr(branch: str) -> co.Serial:
    """
    Triggered by a PR
    """

    src_img = get_src_img(copy_repo=True)
    src_img.path_to_code = "./cicd/remote_microservices"

    print(f"Testing branch indicated by PR in remote env: {test_env_name}")

    return main(src_img, test_env)


def merge() -> co.Serial:
    """
    Triggered from a merge to "main"
    """

    src_img = get_src_img(copy_url=repo, copy_branch=prod_branch)
    src_img.path_to_code = "./cicd/remote_microservices"

    print(f"Testing branch: {prod_branch} in remote env: {test_env_name}")

    prod_env = access.env("prod")
    prod_env_name = prod_env["Name"]

    print(f"...if it passes, will deploy to {prod_env_name}")

    return main(src_img, test_env, prod_env=prod_env)


# Helper for injecting code into the deploy image
def get_src_img(**kwargs):
    return co.Image(
        image=infractl_image,
        reqs_py=["conducto", "sh"],
        reqs_packages=["git", "openssh"],
        **kwargs,
    )


if __name__ == "__main__":

    co.Image.share_directory("remote_microservices", ".")

    # If you're in a sandbox, uncomment only one of these or install
    # condcuto for local control

    # test local code
    co.main(default=testlocal)

    # test code from git branch
    # co.main(argv=["pr", "my_feature"])

    # test code from main branch
    # co.main(default=merge)
