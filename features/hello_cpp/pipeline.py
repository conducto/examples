import conducto as co

CRC = co.ContainerReuseContext

img = co.Image(image="frolvlad/alpine-gxx", copy_dir=".")


def hello() -> co.Serial:

    # Reuse the "build" container for the "test" node
    # so that the binary is available in the second node.
    with co.Serial(
        image=img, container_reuse_context=CRC.NEW, doc=co.util.magic_doc(comment=True)
    ) as root:
        co.Exec("g++ hello.cpp -o hello", name="build")
        co.Exec("./hello | grep 'World!'", name="test")

    return root


if __name__ == "__main__":
    co.main(default=hello)
