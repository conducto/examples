import conducto as co
from inspect import cleandoc
from calendar import monthrange
from datetime import datetime
from textwrap import indent
from sh import fortune as get_fortune


def nodes_for_this_month(now):
    parent = co.Parallel()
    for i in range(monthrange(now.year, now.month)[1]):
        date = f"{now.year}-{now.month}-{i}"
        fortune = get_fortune()

        cmd = cleandoc(
            f"""
            echo "About {date} the spirits say:"
            cat << EOF
            {indent(fortune, prefix='            ')}
            EOF"""
        )
        parent[date] = co.Exec(cmd)
    return parent


def make_pipeline() -> co.Serial:

    root = co.Serial()
    root = nodes_for_this_month(datetime.now())
    return root


if __name__ == "__main__":
    co.main(default=make_pipeline)
