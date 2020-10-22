import conducto as co
import json

# uses the "docker:latest" on dockerhub to run "hello-world:latest" on dockerhub
def hello_referenced() -> co.Serial:

    with co.Serial() as root:
        root["Say Hi"] = co.Exec(
            "docker run hello-world", image="docker", requires_docker=True
        )

    return root


# installs docker via curl, then runs "hello-world:latest" on dockerhub
def hello_installed() -> co.Serial:

    img = co.Image(reqs_docker=True)
    with co.Serial() as root:
        root["Say Hi"] = co.Exec(
            "docker run hello-world", image=img, requires_docker=True
        )

    return root


if __name__ == "__main__":
    co.main(default=hello_referenced)
