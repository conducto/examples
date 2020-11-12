# A normal pipeline definition wouldn't need to hide things from its reader.
# But since this is a tour, we want to keep the definition minimal and show
# hepful text on the pipeline instance and not in the definition too.

import conducto as co
from inspect import cleandoc


def guide(root):
    """
    Attach helpful messages
    """

    root.doc = cleandoc(
        """
        #### A Parallel Parent

        This is a `Parallel` node.

        Unlike last time, its children execute all at once.

        #### Apply an Image to all Children

        The `image` node parameter is inherited by each child.

        Notice that each child uses a custom image named: *my-shared-image*.

        #### Custom Image

        Image parameters enable customizations:

        - clone code into an image with `copy_url` and  `copy_branch`
        - install linux packages with `reqs_packages`
        """
    )

    root["Look around"].doc = cleandoc(
        """
        #### Something is Wrong

        The nodes below rely on:
        - `./hello_py_js`
        - `./hello_cpp`

        If those folders don't show up in **Stdout**, there's a problem.

        """
    )

    root["Hi from Node"].doc = cleandoc(
        """
        #### To Fix It

        Clone the [Conducto examples](https://github.com/conducto/examples) repo instead.
        ```
        copy_url="https://github.com/conducto/examples",
        ```

        After changing the definition, launch a new pipeline with the change.
        """

    )

    root["Hi from C++"].doc = cleandoc(
        """
        #### `g++` is missing

        We can't pick a different base image because we want to keep Node.js.

        Instead, just install the compiler:
        ```
        reqs_packages=["tree", "g++"],
        ```
        """
    )

    root["summary"] = stop_summary()

    return root


def stop_summary():
    return co.Exec(
        ":",
        doc=cleandoc(
            """
            #### Wrong Repo

            The definition called for a git repo to be included in the image.

            A node failed because it referenced software from the wrong git repo.

            The fix was make the image use the right repo.

            #### Missing Dependency

            Another failure was caused by a missing dependency.

            The fix was to make the image install that dependency.

            If all of this pipeline's nodes are green, you've completed this example.

            #### Related Docs:

            - [Tour Map](/docs/getting-started/tour)
            - [Pipeline Structure](/docs/basics/pipeline-structure)
            - [Images](/docs/basics/images)
            - [Hello Git (example)](https://github.com/conducto/examples/blob/main/features/hello_git/pipeline.py)
            - [Hello Native (example)](https://github.com/conducto/examples/tree/main/features/hello_native)


            #### A fork in the road:

            - [Explore how Conducto manipulates Docker containers.](/app/sandbox/github/conducto/examples?dir=tour/reuse&preview_file=pipeline.py)
            - [Call Docker directly from a pipeline node.](/app/sandbox/github/conducto/examples?dir=tour/docker&preview_file=pipeline.py)
            #### Go Back

            - [Hello World](/app/sandbox/github/conducto/examples?dir=tour/hello&preview_file=pipeline.py)

            """
        ),
    )
