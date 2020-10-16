import conducto as co
import json
import os

# we need two custom images
# other images are used unaltered from dockerhub
docker_img = co.Image(image="docker:latest", copy_dir=".", reqs_py=["conducto"])
test_img = co.Image(
    image="python:latest", copy_dir=".", reqs_py=["conducto", "redis", "requests"]
)


# Test Functions
################

# The functions below are called directly by exec nodes in the
# Pipeline Definitions section

def redis_up():
    """
    Is Redis Up?
    """

    # not a dependency of user-side code
    # but required once inside the pipeline
    #(provided by 'reqs_py` kwarg to test_img)
    import redis

    ip = co.data.pipeline.gets("/redis/ip").decode()
    r = redis.Redis(host=ip, port=6379, db=0)
    r.ping()


def flask_up():
    """
    Is Flask Up?
    """

    import requests

    ip = co.data.pipeline.gets("/flask/ip").decode()
    url = f"http://{ip}:5000"
    resp = requests.get(url)
    if resp.status_code >= 300:
        print(resp.text)
        raise Exception(f"flask service responded {resp.status_code}")


def integration_test():
    """
    Do subsequent calls to flask cause an incremented response?
    (a counter is stored in Redis)
    """

    import requests
    import re

    # prep
    ip = co.data.pipeline.gets("/flask/ip").decode()
    url = f"http://{ip}:5000"
    print(url)

    def get_num(resp):
        text = resp.text.strip()
        print("got:", text)
        num = re.search(f"[0-9]+", text).group(0)
        return int(num)

    # two requests
    one = get_num(requests.get(url))
    two = get_num(requests.get(url))

    # did the response increment?
    if (one + 1) == two:
        print("increment detected")
    else:
        raise Exception("got {resp_two} then {resp_one}")

# Pipeline Definitions
######################

# Type hinted functions that return Conducto nodes can be called from the CLI.
# This will create pipeline instances with contents restricted to that function.
# Or call one pipeline-defining function from another to create larger pipelines
# though composition.  Pipeline nodes are python objects.

# To launch a local pipeline from this definition:
# $ python pipeline.py --local

def pipeline() -> co.Serial:
    """
    Starts services, tests them, and cleans up
    """

    # don't stop on errors so that clean up still runs if something goes wrong
    with co.Serial(stop_on_error=False) as root:

        with co.Serial(name="run", stop_on_error=True) as test:

            # start services, sanity-check that they're indeed up
            test["deploy"] = deploy()
            test["test_up"] = test_up()

            # test that they work together
            test["integration test"] = co.Exec(integration_test)
            test["integration test"].image = test_img

        # stop services
        root["clean up"] = teardown()

        # start with cleanup skipped so that app stays deployed
        # manually unskip this node to trigger cleanup
        root["clean up"].skip = True

    return root

# To launch a local pipeline from this definition:
# $ python pipeline.py deploy --local

def deploy() -> co.Parallel:
    """
    Starts services and extracts runtime details
    """
    with co.Serial(image=docker_img, requires_docker=True) as node:

        # use the redis image from dockerhub
        with co.Serial(name="redis") as redis:
            redis["start"] = co.Exec(
                """
                set -euo pipefail
                docker inspect \\
                  $(docker run --rm -d \\
                      --network conducto_network_$CONDUCTO_PIPELINE_ID \\
                      redis:alpine) \\
                  | tee \\
                  | conducto-data-pipeline puts /redis/inspect
                """
            )
            redis["container metadata"] = co.Exec(extract, "redis")

        # incloud our flask code via a Dockerfile
        with co.Serial(name="flask") as flask:
            flask["build"] = co.Exec("docker build . -t myflask:latest")
            flask["start"] = co.Exec(
                """
                set -euo pipefail
                docker inspect \\
                  $(docker run --rm -d \\
                      --network conducto_network_$CONDUCTO_PIPELINE_ID \\
                      -p 5000:5000 \\
                      -e REDIS_IP=$(conducto-data-pipeline gets /redis/ip) \\
                      myflask:latest) \\
                  | tee \\
                  | conducto-data-pipeline puts /flask/inspect
                """
            )
            flask["container metadata"] = co.Exec(extract, "flask")

    return node



# In this example, container id's are stored on the launched pipeline instance.
# Unlike the pipeline-node-returning functions above, the ones below can't be
# called independently from the CLI because the new pipeline wouldn't have the
# data that they need) you could work around this by using `conducto-data-user`
# instead.

def test_up() -> co.Parallel:
    """
    Docker returned, but are the services really up?
    """
    with co.Parallel(image=test_img) as node:
        node["ping redis"] = co.Exec(redis_up)
        node["hit flask"] = co.Exec(flask_up)
    return node

def teardown():
    """
    Stop containers.
    """
    with co.Parallel(image=docker_img, requires_docker=True) as node:
        node["redis"] = co.Exec("docker stop $(conducto-data-pipeline gets /redis/id)")
        node["flask"] = co.Exec("docker stop $(conducto-data-pipeline gets /flask/id)")
    return node

# Helper Functions
##################

def extract(path):
    """
    path: Given a service name like "foo" where pipeline://foo/inspect contains
    the output of docker inspect for that service's container.

    effect:
      - store the container's conducto-facing IP address in /foo/ip.
      - store the container's ID in /foo/id
    """

    inspect_key = f"/{path}/inspect"
    ip_key = f"/{path}/ip"
    id_key = f"/{path}/id"

    # get prerequisite data
    pipeline_id = os.environ["CONDUCTO_PIPELINE_ID"]
    print("key:", inspect_key)
    # sleep(1) # lose the race with node that saves it
    print("val:", co.data.pipeline.gets(inspect_key).decode())
    inspection = json.loads(co.data.pipeline.gets(inspect_key).decode())[0]

    # stash container id too
    co.data.pipeline.puts(id_key, inspection["Id"].encode())

    # get this container's IP address
    network_names = []
    address = None
    for name, network in inspection["NetworkSettings"]["Networks"].items():
        network_names.append(name)
        if pipeline_id in name:
            address = network["IPAddress"]
            print(address)
            co.data.pipeline.puts(ip_key, address.encode())

    if not address:
        raise Exception(
            f"CONDUCTO_PIPELINE_ID = {pipeline_id}, "
            f"but no matching network was found among {json.dumps(network_names)}"
        )


if __name__ == "__main__":

    # this sets "pipeline" as the default pipeline-defining function
    co.main(default=pipeline)
