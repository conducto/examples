import conducto as co

python_img = co.Image(
    image="python:3.8-alpine",
    copy_url="https://github.com/conducto/examples",
    copy_branch="master"
    )

def hello() -> co.Serial:
    pipeline = co.Serial(image=python_img)
    pipeline["Say Hi"] = co.Exec("python hello_py_js/hello.py")
    return pipeline

if __name__ == '__main__':
    co.main(default=hello)
