import conducto as co

python_image = co.Image(image="python:3.8-alpine")
code = 'print("Hello from Python")'
cmd = f"python -c '{code}'"


def hello() -> co.Serial:
    pipeline = co.Serial(image=python_image)
    pipeline["Python Hello"] = co.Exec(cmd)
    return pipeline


if __name__ == "__main__":
    co.main(default=hello)
