import conducto as co
import json

# Call a python-native function from your python pipeline
#########################################################

# ensure the image has the packages we need so it's available from inside a
# pipeline container
py_img = co.Image(
    image="python:3.8-alpine", reqs_py=["conducto", "cowpy"], copy_dir="."
)


# we'll be calling this function directly
def say_it():

    # since this is only called inside the pipeline, whoever launches it doesn't
    # need to have this package installed
    from cowpy.cow import Moose

    print(Moose().milk("Hello World"))


def hello_py() -> co.Serial:

    with co.Serial() as root:
        hi = co.Exec(say_it)
        hi.image = py_img
        root["Say Hi"] = hi

    return root


# Use the package repository native to your image linux flavor
##############################################################

# use `apt` to install `jq` into the image
lin_img = co.Image(reqs_packages=["jq"])

# have it parse some json
def hello_linux() -> co.Serial:
    pipeline = co.Serial()
    pipeline["Say Hi"] = co.Exec(
        """
        echo '{"message": "Hello World"}' | jq '.message'
        """,
        image=lin_img,
    )
    return pipeline


if __name__ == "__main__":
    co.main(default=hello_py)
