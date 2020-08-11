import conducto as co

# appears in screenshot in /docs/basics/images#image-changes

python_img = co.Image(image='python:3.8-alpine', copy_dir='.')

def hello() -> co.Serial:
    with co.Serial() as pipeline:
        pipeline["Say Hi"] = co.Exec('python hello_mod.py', image=python_img)
    return pipeline


if __name__ == '__main__':
    co.main(default=hello)
