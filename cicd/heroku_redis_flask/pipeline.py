"""
### Heroku + Redis + Flask CI/CD Pipeline

This is a CI/CD pipeline that uses Heroku to deploy and test a Flask app
that talks to Redis.

You must have Heroku and RedisLabs accounts and specify the following as
secrets in the Conducto app, or in the environment:
* HEROKU_API_KEY
* REDIS_HOST
* REDIS_PORT
* REDIS_PASSWORD
"""

import conducto as co

########################################################################
# Pipeline Defintion
########################################################################


def main() -> co.Serial:
    image = co.Image(dockerfile="./Dockerfile", copy_dir=".")
    with co.Serial(doc=__doc__, image=image, env=get_env()) as root:
        with co.Parallel(name="access check") as access_check:
            access_check["Heroku"] = co.Exec(TEST_HEROKU)
            access_check["RedisLabs"] = co.Exec(TEST_REDIS)
        root["deploy"] = deploy()
        root["integration test"] = co.Exec(INTEGRATION_TEST)
        with co.Parallel(name="teardown") as teardown:
            teardown["clear data"] = co.Exec(CLEAR_DATA)
            teardown["stop"] = co.Exec(STOP_APP)
            teardown["destroy"] = co.Exec(DESTROY_APP)
    return root


def deploy() -> co.Serial:
    with co.Serial() as node:
        node["create app"] = co.Exec(CREATE_APP)
        node["stop if not already"] = co.Exec(STOP_APP)
        node["configure app"] = co.Exec(CONFIGURE_APP)
        # CRC.NEW means that all nodes in "push" run in the same container.
        CRC = co.ContainerReuseContext
        with co.Serial(container_reuse_context=CRC.NEW, name="push") as push:
            push["register ssh key"] = co.Exec(REGISTER_SSH_KEY)
            push ["test ssh key"] = co.Exec(TEST_SSH_KEY)
            push["push code"] = co.Exec(PUSH_CODE)
        node["start app"] = co.Exec(START_APP)
        with co.Parallel(name="sanity check") as check:
            check["peek at logs"] = co.Exec(PEEK_LOGS)
            check["check alive"] = co.Exec(TEST_FLASK)
    return node


def get_env():
    # TODO: It is better to specify your AWS credentials as secrets in the
    # Conducto app, but if you want to quickly test this pipeline, you can
    # inject your credentials as environment variables here.
    env = {}
    #env = {
    #    "HEROKU_API_KEY": "",
    #    "REDIS_HOST": "",
    #    "REDIS_PORT": "",
    #    "REDIS_PASSWORD": "",
    #}
    from uuid import uuid4
    random_id = str(uuid4())[:6]
    env["APP_NAME"] = f"conducto-demo-app-{random_id}"
    env["TAG"] = "conducto-demo-tag"
    return env


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
if heroku apps | grep "$APP_NAME" > /dev/null
then
    echo "found $APP_NAME"
else
    heroku apps:create "$APP_NAME"
fi
"""

PUSH_CODE = """
set -euxo pipefail

# configure git 
git init
git config --global user.email "fake-user@example.com"
git config --global user.name "fake-user"
git config --global url.ssh://git@heroku.com/.insteadOf https://git.heroku.com/
heroku git:remote -a "$APP_NAME"

# push code to heroku
git add app
git commit -m "pushing to heroku"
git push -f heroku master 2>&1 \\
    | tee /dev/fd/2 \\
    | tee remote_logs \\
    | grep 'Verifying deploy... done'
"""

CONFIGURE_APP = """
set -eux
heroku config:set \\
    TAG=$TAG \\
    REDIS_HOST=$REDIS_HOST \\
    REDIS_PORT=$REDIS_PORT \\
    REDIS_PASSWORD=$REDIS_PASSWORD \\
    -a $APP_NAME
"""

REGISTER_SSH_KEY = """
set -ex

# First generate an ssh key.
# Alternatively, have an ssh key already saved to your secrets and skip this part.
ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519
chmod 600 /root/.ssh/id_ed25519

# Add ssh key to heroku.
heroku keys:add /root/.ssh/id_ed25519.pub
"""

TEST_SSH_KEY = """
set -ex
ssh -v -i /root/.ssh/id_ed25519 -o StrictHostKeyChecking=no -T git@heroku.com >out 2>&1 || true
grep -v "Permission denied" out
grep "Authentication succeeded" out
"""

START_APP = """
set -eux
heroku ps:scale web=1 -a "$APP_NAME"
"""

PEEK_LOGS = """
set -euxo pipefail
sleep 3

heroku logs -a "$APP_NAME" \\
    | tail -n 30 \\
    | tee log_snippet 1>&2

grep -i 'starting gunicorn' log_snippet
grep -i 'listening' log_snippet
"""

TEST_FLASK = """
set -ex
FLASK_URL=$(heroku apps:info -a $APP_NAME | grep "Web URL" | egrep -o "https://[^ ]*")
curl -vf $FLASK_URL
"""

INTEGRATION_TEST = """
set -ex

# Make two requests for flask.
FLASK_URL=$(heroku apps:info -a $APP_NAME | grep "Web URL" | egrep -o "https://[^ ]*")
curl -s $FLASK_URL | egrep -o '[0-9]+' > first
curl -s $FLASK_URL | egrep -o '[0-9]+' > second

# Did they increment?
let FIRST_PLUS_ONE="$(cat first)+1"
cat second | grep $FIRST_PLUS_ONE
"""

CLEAR_DATA = """
set -eux
redis-cli -h "$REDIS_HOST" \\
          -p "$REDIS_PORT" \\
          -a "$REDIS_PASSWORD" del "$TAG"
"""

STOP_APP = """
set -eux
heroku ps:scale web=0 -a "$APP_NAME" || true
"""

DESTROY_APP = """
set -eux
heroku apps:destroy -a "$APP_NAME" --confirm="$APP_NAME"
"""

if __name__ == "__main__":
    co.Image.share_directory("remote_microservices", ".")
    co.main(default=main)
