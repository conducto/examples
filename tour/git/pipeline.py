import conducto as co
import tour


def pipeline() -> co.Parallel:
    """
    Customize an Image
    """

    # the previous example passed a string via the `image` node parameter
    #
    #     root["world]"] = co.Exec(f"{cmd}",
    #                              image="node:current-alpine")
    #                                     ^
    # like this --------------------------┘

    # pass co.Image objects for more options
    img = co.Image(
        name="my-shared-image",
        image="node:current-alpine",
        install_packages=["tree"],
        copy_url="https://github.com/conducto/conducto",
        copy_branch="main",
    )

    # set the `image` node parameter on a parent
    # the children will inherit the value
    root = co.Parallel(image=img)

    # this node runs ok
    root["Look around"] = co.Exec(
        """
        tree -L 2 ;
        find . -name 'hello_.*'
        """)

    # these nodes have problems
    root["Hi from Node"] = co.Exec("node hello_py_js/hello.js")
    root["Hi from C++"] = co.Exec(
        """
        g++ hello_cpp/hello.cpp -o hello ;
        ./hello
        """
    )

    # explore the pipeline to understand them

    # change this file, and relaunch the pipeline to see results

    root = tour.guide(root)

    return root


if __name__ == "__main__":
    co.main(default=pipeline)
