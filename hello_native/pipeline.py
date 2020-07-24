import conducto as co

# highlight-start
from cowpy.cow import Moose

img = co.Image(image="python:3.8-alpine", reqs_py=["conducto", "cowpy"], copy_dir=".")
# highlight-end


def say_it():
    # highlight-start
    print(Moose().milk("Hello World"))
    # highlight-end


def hello() -> co.Serial:
    pipeline = co.Serial(image=img)
    pipeline["Say Hi"] = co.Exec(say_it)
    return pipeline


if __name__ == "__main__":
    co.main(default=hello)
