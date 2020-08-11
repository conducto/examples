import conducto as co
from inspect import cleandoc

# sleep for the indicated time
# write 1 to disk if the file 'i' doesn't exist
# increment the number in that file if it does
def inc_sleep(sleep):
    return cleandoc(
        f"""
        sleep {sleep}
        if [ ! -f i ]
        then
            echo 1 | tee i
        else
            WAS=$(cat i)
            NEXT=$(($WAS + 1))
            echo $NEXT | tee i
        fi
        """
    )

# fail if the contents of the file 'i' isn't 2
def test(expected):
    return cleandoc(
        f"""
        if [ ! -f i ]
        then
            echo "file 'i' not found"
            exit 1
        else
            cat i | tee /dev/fd/2 | grep {expected}
            exit $?
        fi
        """
    )


# creates nodes that test for `same-container`-ness
# this attaches them to the node created by the function call's enclosing context manager
def nodes(n, t=0, new_each=False):

    # increment the contents of a file, with a delay
    for i in range(1, n + 1):
        if new_each:
            co.Exec(inc_sleep(t), name=f"{i}", same_container=co.SameContainer.NEW)
        else:
            co.Exec(inc_sleep(t), name=f"{i}")
    co.Exec(test(i), name=f"={i}?")

def parallel_batches(n_str) -> co.Parallel:

    n = int(n_str)

    with co.Serial(stop_on_error=False) as root:
        with co.Parallel(name="unset"):
            nodes(n)
        with co.Parallel(name="new parent", same_container=co.SameContainer.NEW):
            nodes(n, new_each=True)
        with co.Parallel(name="new children"):
            nodes(n, new_each=True)

    return root


def serial_batches() -> co.Parallel:

    n = 3

    with co.Serial(stop_on_error=False) as root:
        with co.Serial(name="first unset"):
            nodes(n)
        with co.Serial(name="second unset"):
            nodes(n)
        with co.Serial(name="new", same_container=co.SameContainer.NEW):
            nodes(n)
        with co.Serial(name="new with escape", same_container=co.SameContainer.NEW):
            nodes(n)
            with co.Serial(name="escape A", same_container=co.SameContainer.ESCAPE):
                nodes(n)
            with co.Serial(name="escape B", same_container=co.SameContainer.ESCAPE):
                nodes(n)

    return root

if __name__ == "__main__":
    co.main()
