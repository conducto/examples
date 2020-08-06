import conducto as co

python_img = co.Image(
    image="python:3.8-alpine",
    copy_url="https://github.com/leachim6/hello-world",
    copy_branch="master",
    path_map={"./local-copy/p": "p"},
)

def hello() -> co.Serial:
    pipeline = co.Serial()
    pipeline["Say Hi"] = co.Exec("python p/python3.py", image=python_img)
    return pipeline

if __name__ == "__main__":
    co.main(default=hello)
