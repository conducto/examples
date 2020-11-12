import conducto as co
from random import random

# how many nodes in a test?
n = 3

# write 1 to disk if the file 'i' doesn't exist
# increment the number in that file if it does
# if rand is True, sleep for a random interval between 0 and 3 seconds first
def inc_sleep(rand):

    cmd = f"""
          if [ ! -f i ]
          then
              NEXT=1
          else
              WAS=$(cat i)
              NEXT=$(($WAS + 1))
          fi
          echo $NEXT | tee i
          """

    if not rand:
        return cmd
    else:
        sleep = random() * 3
        return f"sleep {sleep}\n" + command


# fail if the contents of the file 'i' isn't expected
def test(expected):
    return f"""
           if [ ! -f i ]
           then
               echo "file 'i' not found"
               exit 1
           else
               cat i | tee /dev/fd/2 | grep {expected}
               exit $?
           fi
           """


# creates nodes that test for `same-container`-ness
# this attaches them to the node created by the function call's enclosing context manager
def nodes(n, t=0, new_each=False, rand=False):

    # increment the contents of a file, with a delay
    for i in range(1, n + 1):
        if new_each:
            co.Exec(
                inc_sleep(rand),
                name=f"{i}",
                container_reuse_context=co.ContainerReuseContext.NEW,
            )
        else:
            co.Exec(inc_sleep(rand), name=f"{i}")

    # test if the expected value is found
    if new_each:
        co.Exec(
            test(i), name=f"={i}?", container_reuse_context=co.ContainerReuseContext.NEW
        )
    else:
        co.Exec(test(i), name=f"={i}?")


# explores how container_reuse_context works among Parallel nodes
def parallel(n_str) -> co.Parallel:

    n = int(n_str)

    with co.Serial(stop_on_error=False) as root:
        with co.Parallel(name="unset"):
            nodes(n, rand=True)
        with co.Parallel(
            name="new parent", container_reuse_context=co.ContainerReuseContext.NEW
        ):
            nodes(n, rand=True)
        with co.Parallel(name="new children"):
            nodes(n, new_each=True, rand=True)

    return root


# container_reuse_context not specified, passive reuse might be unexpected
def default_serial() -> co.Parallel:

    with co.Serial(stop_on_error=False) as root:
        with co.Serial(name="first unset"):
            nodes(n)
        with co.Serial(name="second unset"):
            nodes(n)

    return root


# container_reuse_context used to prevent unexpected reuse, but preserve expected reuse
def fixed_serial() -> co.Parallel:

    with co.Serial(stop_on_error=False) as root:
        with co.Serial(
            name="first", container_reuse_context=co.ContainerReuseContext.NEW
        ):
            nodes(n)
        with co.Serial(
            name="second", container_reuse_context=co.ContainerReuseContext.NEW
        ):
            nodes(n)

    return root


# container_reuse_context used to prevent any reuse
def isolated_serial() -> co.Parallel:

    with co.Serial(stop_on_error=False) as root:
        with co.Serial(name="isolated", stop_on_error="False"):
            nodes(n, new_each=True)

    return root


# explores how container_reuse_context's GLOBAL option works
def nested() -> co.Parallel:

    with co.Parallel() as root:
        nodes(n)  # global by default
        with co.Serial(
            name="local", container_reuse_context=co.ContainerReuseContext.NEW
        ):
            nodes(n)
            with co.Serial(
                name="nested global",
                container_reuse_context=co.ContainerReuseContext.GLOBAL,
            ):
                nodes(n)

    return root


if __name__ == "__main__":
    co.main()
