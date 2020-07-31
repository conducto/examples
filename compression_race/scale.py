import conducto as co
from math import ceil

# generate five randomly generated payloads
# ranging in size from 50m to 250m
# also install gnu parallel
payloads = co.Image(dockerfile="Dockerfile", context=".")


def _add_nodes(parent, n):
    for i in range(n):
        child_name = f"worker {str(i)}"
        parent[child_name] = co.Exec(
            f"gzip -1 payload{(i % 5) + 1}.dat",
            cpu=1,
            same_container=co.SameContainer.NEW,
        )


def race(n) -> co.Serial:
    n = int(n)
    with co.Serial(image=payloads, cpu=2) as root:

        # add an arbitrary number of parallel nodes
        # one cpu for each
        with co.Parallel(name="node parallelism") as parent:
            _add_nodes(parent, n)

        # add an arbitrary number of parallel processes
        # use that many cpu's
        targets = "\n".join([f"payload{(i % 5) + 1}.dat" for i in range(n)])
        root["process parallelism"] = co.Exec(
            f"echo '{targets}' " "| parallel gzip {} -k -1 --suffix=.{#}.gz", cpu=4
        )

    return root


if __name__ == "__main__":

    # needed for --cloud
    # hopefully we can infer this from 'context=' above
    # once that happens it can be removed
    co.Image.register_directory("conducto_examples", "..")
    co.main()
