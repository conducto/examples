import conducto as co


def main() -> co.Serial:
    img = co.Image(
        "python:3.8-slim",
        copy_dir=".",
        reqs_py=["conducto", "flask", "black"],
        reqs_packages=["curl"],
        reqs_docker=True,
    )
    with co.Serial(image=img) as root:
        with co.Parallel(name="Init"):
            co.Exec("docker build -t my_image .", name="Build", requires_docker=True)
            co.Exec("black --check .", name="Lint")
            co.Exec("python test.py --verbose", name="UnitTest")
        root["Deploy"] = co.Exec(DEPLOY_CMD, requires_docker=True)
        root["IntegrationTest"] = co.Exec(INTEGRATION_TEST_CMD)
        root["Cleanup"] = co.Exec("docker kill my_app", requires_docker=True)
    return root


# In reality you would deploy this to Heroku, K8s, ECS, or
# something similar. For demo purposes, just start container
# on local machine.
DEPLOY_CMD = """
set -ex

# Kill previous container, if any
docker container rm my_app 2>/dev/null || true

# Run container anew
docker run -d --name my_app my_image

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
    co.main(default=main)
