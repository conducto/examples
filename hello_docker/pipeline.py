import conducto as co

img = co.Image(image="alpine@sha256:185518070891758909c9f839cf4ca393ee977ac378609f700f60a771a2dfe321")

def hello() -> co.Serial:
    with co.Serial(image=img) as pipeline:
        co.Exec("echo hi", name="hi")
    return pipeline

if __name__ == "__main__":
    co.main(default=hello)
