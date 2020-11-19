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

from collections import namedtuple
import conducto as co

# see access.py for auth stuff
import access


def main(touch_prod: bool, code_source: str) -> co.Serial:
    """
    Test the code, deploy if appropriate.
    """

    # determine where the code should come from and where it's going
    params = plan(touch_prod, code_source)

    with co.Serial(doc=__doc__) as root:

        # can we autenticate?  If not, fail early.
        root["access check"] = access_check(params)

        with co.Serial(name="test", env=params.test_env) as test:

            test["deploy"] = deploy(params, test_env=True)
            test["test"] = co.Exec(INTEGRATION_TEST_CMD)

        # will be skipped if prod deploy isn't called for
        root["deploy"] = deploy(params)

        # will start skipped.  Manually unskip to undeploy.
        # root["teardown"] = teardown_all(params)

        # uncommenting "teardown" causes "access check" to have no env vars
        # why?

    return root


# These parameters determine:
#  - local code or repo code?
#  - test only or test + deploy
Plan = namedtuple("Plan", "src_image test_image src_path test_env target_env")


def plan(touch_prod: bool, code_source: str) -> Plan:
    """
    Initialize parameters depending on how the pipeline is to be launched
    """

    def get_src_img(**kwargs):
        return co.Image(image="finalgene/heroku-cli", reqs_packages=["git"], **kwargs)

    test_img = co.Image(reqs_packages=["redis", "curl"])
    test_env = access.env("test")
    test_env_name = test_env["NAME"]

    repo = "https://github.com/conducto/examples"
    branch = code_source

    # where should the code come from?
    if code_source.lower() == "filesystem":

        print(f"Testing code from local filesystem in {test_env_name}")
        src_img = get_src_img(copy_dir=".")
        src_path = "."

    elif code_source.lower() == "pr":

        print(f"Testing branch indicated by PR in {test_env_name}")
        src_img = get_src_img(copy_repo=True)
        src_path = "./cicd/remote_microservices"

    else:

        print(f"Testing code from {repo}:{branch} in {test_env_name}")
        src_img = get_src_img(copy_url=repo, copy_branch=branch)
        src_path = "./cicd/remote_microservices"

    if touch_prod:
        # CI + CD
        target_env = access.env("prod")
        target_name = target_env["NAME"]
        print(f"If it passes, will deploy to {target_name}")

    else:
        # Just CI
        target_env = test_env

    return Plan(src_img, test_img, src_path, test_env, target_env)


def access_check(params: Plan) -> co.Parallel:
    """
    Test available credentials against infra providers.
    """

    with co.Parallel(env=params.test_env) as node:
        node["Heroku"] = co.Exec(TEST_HEROKU_CMD, image=params.src_image)

        node["RedisLabs"] = co.Exec(TEST_REDIS_CMD, image=params.test_image)

    return node


def deploy(params: Plan, test_env=False) -> co.Serial:
    """
    Put the code in an environment.
    Which code is determed by param.src_image
    Which environment is determed by target_env
    """

    # pick correct deploy target
    if test_env:
        env = params.test_env
    else:
        env = params.target_env

        # did a previous node already deploy here?
        if env == params.test_env:

            # do nothing
            doc = "This is not a CD pipeleine"
            with co.Serial(doc=doc) as node:
                co.Exec(":", name=access.uniqstr("prod"), skip=True, doc=doc)
            return node

    # onward to production
    with co.Serial(image=params.src_image) as node:
        with co.Serial(name=env["NAME"]) as deploy:
            deploy["create"] = co.Exec(CREATE_APP_CMD)
            deploy["push"] = co.Exec(PUSH_CODE_CMD.format(params.src_path))

        # was the deploy successful?
        node["sanity check"] = co.Exec(TEST_FLASK_CMD)

    return node


def teardown_all(params: Plan):
    """
    Unskip a child to un-deploy an environment.
    """

    def teardown_one(env):
        with co.Parallel(name=env["NAME"], env=env) as down:
            down["clear data"] = co.Exec(CLEAR_DATA_CMD, image=params.test_image)
            down["stop flask"] = co.Exec(STOP_FLASK_CMD, image=params.src_image)

    with co.Parallel(skip=True) as teardown:

        # only offer to teardown both environments if they're distinct
        teardown_one(params.test_env)
        if params.test_env != params.target_env:
            teardown_one(params.target_env)

    return teardown


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
# capture latest app clode
cd {}
git init
heroku git:remote -a "$NAME"

# push it to heroku
REV=$(git rev-parse HEAD)
git add -A
git commit -m "conducto/examples@$REV"
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

#   python pipeline.py test_uncommitted --local --run
def test() -> co.Serial:
    """
    Test changes before pushing them
    """
    return main(touch_prod=False, code_source="filesystem")


#   python pipeline.py pr from_branch --cloud --run
def pr(branch: str) -> co.Serial:
    """
    Triggered from a PR
    or when testing CI by hand
    """
    return main(touch_prod=False, code_source="pr")


#   python pipeline.py merge --cloud --run
def merge() -> co.Serial:
    """
    Triggered from a merge
    or when testing CD by hand
    """

    return main(touch_prod=True, code_source="main")


#   python pipeline.py
if __name__ == "__main__":

    # If you're in a sandbox, uncomment only one of these or install
    # condcuto for local control

    # test local code
    co.main(default=test)

    # test code from git branch
    # co.main(argv=["pr", "my_feature"])

    # test code from main branch
    # co.main(default=merge)
