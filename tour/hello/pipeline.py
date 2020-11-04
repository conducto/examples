import conducto as co

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
    root["hello"] = co.Exec(
        f"python -c '{py_code}'",
        doc="Run some Python code")

    # this one has a problem
    root["world"] = co.Exec(
        f"echo '{js_code}' | node -",
        #image="node:current-alpine"
        doc="Run some Javascript via Node.js")
    )

    # to understand the problem, explore the pipeline -->
    # or see README.md for more guidance

    # to fix it:
    # - uncomment the 'image' kwarg
    #
    # then:
    # - save this file (<Ctrl> + S)
    # - reset the failed node

    return root


if __name__ == "__main__":
    co.main(default=pipeline)
