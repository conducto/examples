"""
### Two Local Microservices

This pipeline tests connectivity between two microservices.

The test involves sending an http request to flask, which increments a
counter in redis.  Flask responds with the new value of that counter.

It deploys to the local docker instance, which is atypical for CI/CD,
but makes for a self-contained example.
"""

import conducto as co


def main() -> co.Serial:
    """
    Starts services, tests them, and cleans up
    """

    # outer context: continue on errors
    # so 'clean up' still runs if tests fail
    with co.Serial(stop_on_error=False, doc=__doc__) as root:

        # inner context: stop on errors
        # don't bother testing a failed deployment
        with co.Serial(name="run", stop_on_error=True) as run:
            run["deploy"] = deploy()
            run["test"] = test()

        # stop services
        root["clean up"] = teardown()

    return root


# test tools
test_img = co.Image(install_packages=["redis", "curl"], install_pip=["conducto"])


def test() -> co.Serial:
    """
    Check if both redis and flask are available.  Then see if they're
    working.
    """

    with co.Serial(image=test_img) as test:

        with co.Parallel(name="services up?") as check:
            check["redis up?"] = co.Exec(TEST_REDIS_CMD)
            check["flask up?"] = co.Exec(TEST_FLASK_CMD)

    test["integration test"] = co.Exec(INTEGRATION_TEST_CMD)
    return test


# deployment tools
docker_img = co.Image("docker:latest", install_pip=["conducto"], copy_dir=".")


def deploy() -> co.Parallel:
    """
    Start Containers.
    """

    with co.Serial(image=docker_img, requires_docker=True) as node:
        # Flask needs to know the Redis IP before it can start, so
        # make sure this node is Serial.

        # use the redis image from dockerhub
        with co.Serial(name="redis") as redis:
            redis["start"] = co.Exec(START_REDIS_CMD)

        # include our flask code via a Dockerfile
        with co.Serial(name="flask") as flask:
            flask["build"] = co.Exec(BUILD_FLASK_CMD)
            flask["start"] = co.Exec(START_FLASK_CMD)

    return node


def teardown():
    """
    Stop containers.
    """
    with co.Parallel(image=docker_img, requires_docker=True) as node:
        node["stop redis"] = co.Exec(STOP_REDIS_CMD)
        node["stop flask"] = co.Exec(STOP_FLASK_CMD)
    return node


########################################################################
# Commands
########################################################################

START_REDIS_CMD = """
set -euxo pipefail

# Kill previous container, if any
docker container rm my_redis 2>/dev/null || true

# Run container on pipeline network
docker run --rm -d \\
       --name my_redis \\
       --network conducto_network_${CONDUCTO_PIPELINE_ID} \\
       redis:alpine

# Stash its IP for testing
docker inspect my_redis \\
    --format '{{index .NetworkSettings.Networks "conducto_network_'$CONDUCTO_PIPELINE_ID'" "IPAddress" }}' \\
    > /conducto/data/pipeline/redis_ip
"""

TEST_REDIS_CMD = """
set -ex
REDIS_IP=$(cat /conducto/data/pipeline/redis_ip)
redis-cli -h $REDIS_IP -p 6379 ping | grep PONG
"""

BUILD_FLASK_CMD = "docker build . -t myflask:latest"

START_FLASK_CMD = """
set -euxo pipefail

# Kill previous container, if any
docker container rm my_flask 2>/dev/null || true

# Run container on pipeline network
docker run --rm -d \\
      --name my_flask \\
      --network conducto_network_${CONDUCTO_PIPELINE_ID} \\
      -p 5000:5000 \\
      -e REDIS_IP=$(cat /conducto/data/pipeline/redis_ip) \\
      myflask:latest

# Stash its IP for testing
docker inspect my_flask \\
    --format '{{index .NetworkSettings.Networks "conducto_network_'$CONDUCTO_PIPELINE_ID'" "IPAddress" }}' \\
    > /conducto/data/pipeline/flask_ip
"""

TEST_FLASK_CMD = """
set -ex
FLASK_IP=$(cat /conducto/data/pipeline/flask_ip)
curl $FLASK_IP:5000
"""

INTEGRATION_TEST_CMD = """
set -ex

# two requests for flask
FLASK_IP=$(cat /conducto/data/pipeline/flask_ip)
curl -s $FLASK_IP:5000 | egrep -o '[0-9]+' > first
curl -s $FLASK_IP:5000 | egrep -o '[0-9]+' > second

# did they increment?
let FIRST_PLUS_ONE="$(cat first)+1"
cat second | grep $FIRST_PLUS_ONE
"""

STOP_REDIS_CMD = "docker stop my_redis"

STOP_FLASK_CMD = "docker stop my_flask"

if __name__ == "__main__":
    co.main(default=main)
