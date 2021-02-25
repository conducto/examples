"""
### Simple CI/CD Pipeline

This is a CI/CD pipeline that builds and tests a simple flask
microservice, deploys it locally, then tests the deployment.
"""

import conducto as co

########################################################################
# Pipeline Definition
########################################################################


def main() -> co.Serial:
    with co.Serial(image=get_image(), doc=__doc__) as root:
        with co.Parallel(name="Initialize"):
            co.Exec("docker build -t my_image .", name="Build", requires_docker=True)
            co.Exec("black --check .", name="Lint")
            co.Exec("python test.py --verbose", name="Unit Test")
        root["Deploy"] = co.Exec(DEPLOY_CMD, requires_docker=True)
        root["Integration Test"] = co.Exec(INTEGRATION_TEST_CMD)
        root["Cleanup"] = co.Exec("docker kill my_app", requires_docker=True)
    return root


def get_image():
    return co.Image(
        "python:3.8-slim",
        copy_dir=".",
        install_pip=["flask", "black"],
        install_packages=["curl", "vim"],
        install_docker=True,
    )


########################################################################
# Commands
########################################################################

# In reality you would deploy this to Heroku, K8s, ECS, or
# something similar. For demo purposes, just start container
# on local machine.
DEPLOY_CMD = """
set -ex

# Kill previous container, if any
docker container rm my_app 2>/dev/null || true

# Run container anew
dockerr run -d --name my_app my_image

# Print logs and make sure it launched successfully
sleep 2
docker logs --details my_app
rc=$(docker inspect my_app --format='{{.State.ExitCode}}')
test $rc -eq 0
"""

# If you had actually deployed to one of the above services,
# you would `curl` to its actual URL. In this case, just
# launch on this host and curl against localhost.
INTEGRATION_TEST_CMD = """
set -ex

# Run the sever, wait for it to boot up, query it, then kill it
flask run &
sleep 2
OUTPUT=$(curl -s localhost:5000)
kill %1

# Verify that the output is what's expected
test "$OUTPUT" == 'Hello, Conducto!'
"""


if __name__ == "__main__":
    co.Image.share_directory("flask_microservice", ".")
    co.main(default=main)
