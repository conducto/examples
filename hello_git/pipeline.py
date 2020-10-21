import conducto as co

# Include an external git repo in the image
############################################

external_img = co.Image(
    image="python:3.8-alpine",
    copy_url="https://github.com/leachim6/hello-world",
    copy_branch="master",
)

# reference code in that repo
def hello_other() -> co.Serial:
    pipeline = co.Serial(image=external_img)
    pipeline["Say Hi"] = co.Exec("python p/python3.py")
    return pipeline

# Include this git repo in the image
#####################################

examples_img = co.Image(image="python:3.8-alpine", copy_repo=True, reqs_py=['conducto'])

# plucks the hello-world pipeline out of it
def get_pipeline() -> co.Serial:
    from hello_world import hello
    return hello.pipeline()


# reference code in this repo
def hello_self() -> co.Serial:
    pipeline = co.Serial(image=examples_img, env={"PYTHONPATH":"."})
    pipeline["Say Hi"] = co.Lazy(get_pipeline)
    return pipeline

# co.Lazy builds the rest of the pipeline tree at runtime, so if new nodes are
# added to ../hello_world.pipeline.py in the future, those nodes will show up
# without needing to change this file

if __name__ == "__main__":
    co.main(default=hello_other)
