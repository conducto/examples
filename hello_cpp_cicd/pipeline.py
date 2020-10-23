import conducto as co

CRC = co.ContainerReuseContext
from enum import Enum

build_img = co.Image(dockerfile="./build/Dockerfile", reqs_py=["conducto"])
test_img = co.Image(dockerfile="./test/Dockerfile", reqs_py=["conducto"])


class BuildType(Enum):
    DEBUG = "debug"
    RELEASE = "release"

def get(build_type):
    return {
        BuildType.DEBUG: {"config-flags": "-g", "build-dir": "debug"},
        BuildType.RELEASE: {"config-flags": "-gr", "build-dir": "release"},
    }[build_type]


def build(build_type: BuildType) -> co.Serial:
    with co.Serial(container_reuse_context=CRC.NEW, image=build_img) as node:
        co.Exec(
            f'./configure.sh {get(build_type)["config-flags"]}',
            name="set up build environment",
        )
        cd_and = f'cd {get(build_type)["build-dir"]} && '
        co.Exec(cd_and + "make", name="build c++ code")
        co.Exec(cd_and + "make test", name="unit tests")
        co.Exec(cd_and + "make package", name="make .deb package")
        co.Exec(cd_and + "dpkg -c hello*.deb", name="show package contents")
        co.Exec(
            cd_and + "conducto-data-pipeline put thepkg hello_*.deb",
            name="stash package for use elsewhere",
        )

    return node


def test() -> co.Serial:
    with co.Serial() as node:
        node["build"] = build(BuildType.RELEASE)
        with co.Serial(container_reuse_context=CRC.NEW) as tests:
            co.Exec(
                "conducto-data-pipeline get thepkg pkg.deb", name="get built package"
            )
            for distro in ["ubuntu:16.04"]:
                co.Exec(
                    'docker run -v "./pkg.deb:/root/pkg.deb {distro} bash -c "dpkg -i pkg.deb && hello" | grep "Hello World!"',
                    name=distro,
                )
        node["tests"] = tests
    return node


if __name__ == "__main__":
    co.main()
