"""
This example has three identical pipelines, each is specified in a different syntax.
"""
import conducto as co

foo = co.Image(name="foo")
bar = co.Image(name="bar")


def dict() -> co.Serial:
    """
    Each Node is [dict-like](/docs/basics/pipeline-structure#dict), and you can
    build a hierarchy by assigning children into them.
    """
    root = co.Serial(image="foo", doc=co.util.magic_doc())
    root["all together"] = co.Parallel()
    root["all together"]["a"] = co.Exec("echo step 1, image bar", image="bar")
    root["all together"]["b"] = co.Exec("echo step 1, image foo")
    root["one at a time"] = co.Serial(image="bar")
    root["one at a time"]["c"] = co.Exec("echo step 2, image bar")
    root["one at a time"]["d"] = co.Exec("echo step 3, image bar")
    return root


def path() -> co.Serial:
    """
    The Node tree can be accessed with file system-like
    [paths](/docs/basics/pipeline-structure#path).
    """
    root = co.Serial(image="foo", doc=co.util.magic_doc())
    root["all together"] = co.Parallel()
    root["all together/a"] = co.Exec("echo step 1, image bar", image="bar")
    root["all together/b"] = co.Exec("echo step 1, image foo")
    root["one at a time"] = co.Serial(image="bar")
    root["one at a time/c"] = co.Exec("echo step 2, image bar")
    root["one at a time/d"] = co.Exec("echo step 3, image bar")
    return root


def context() -> co.Serial:
    """
    You can use [context managers](/docs/basics/pipeline-structure#context)
    (Python's `with` statement) to add children. This lets you use whitespace
    to express node depth.
    """
    with co.Serial(image=foo, doc=co.util.magic_doc()) as root:
        with co.Parallel(name="all together"):
            co.Exec("echo step 1, image bar", name="a", image=bar)
            co.Exec("echo step 1, image foo", name="b")
        with co.Serial(name="one at a time", image=bar) as two:
            co.Exec("echo step 2, image bar", name="c")
            co.Exec("echo step 3, image bar", name="d")
        return root


if __name__ == "__main__":
    co.main()
