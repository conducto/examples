import conducto as co

img = co.Image(dockerfile="Dockerfile")


def hello() -> co.Serial:
    with co.Serial(image=img) as pipeline:
        pipeline["Say Hi"] = co.Exec("pokemonsay -n -p Oddish 'Hi'")
    return pipeline


if __name__ == "__main__":
    co.main(default=hello)
