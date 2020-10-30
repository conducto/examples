import conducto as co
import tour

def pipeline() -> co.Serial:
    """
    Welcome to Conducto
    """

    # this example runs the code below in separate containers
    py_code = 'print("Hello")'
    js_code = 'console.log("World!")'

    # commands are stored in a tree
    root = co.Serial()

    # this leaf runs ok
    root["hello"] = co.Exec(f"python -c '{py_code}'")

    # this one has a problem
    root["world"] = co.Exec(
        f"echo '{js_code}' | node -",
        #image="node:current-alpine"
    )

    # explore the pipeline to understand the problem

    # uncomment the 'image' kwarg to fix it

    # then relaunch the pipeline:
    #
    #     <Ctrl> + S       - save the file
    #     <Esc>            - defocus the editor
    #     <Ctrl> + <Enter> - try the fix

    root = tour.guide(root)     # nothing to see here

    return root


if __name__ == "__main__":
    co.main(default=pipeline)
