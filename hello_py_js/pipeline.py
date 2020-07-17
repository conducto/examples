import conducto as co

# https://hub.docker.com/_/pythong?tab=description
python_img = co.Image(image='python:3.8-alpine', copy_dir='.')

# https://hub.docker.com/_/node?tab=description
node_img = co.Image(image='node:current-alpine', copy_dir='.')


def hello() -> co.Serial:
    with co.Serial() as pipeline:
        pipeline["Python Hello"] = co.Exec('python hello.py', image=python_img)
        pipeline["Javascript Hello"] = co.Exec('node hello.js', image=node_img)
    return pipeline


if __name__ == '__main__':
    co.main(default=hello)
