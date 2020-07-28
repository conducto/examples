# tree.py
import conducto as co

foo = co.Image(name="foo")
bar = co.Image(name="bar")

def dict() -> co.Serial:
    root = co.Serial(image="foo")
    root['all together'] = co.Parallel()
    root['all together']['a'] = co.Exec("echo step 1, image bar", image="bar")
    root['all together']['b'] = co.Exec("echo step 1, image foo")
    root['one at a time'] = co.Serial(image="bar")
    root['one at a time']['c'] = co.Exec("echo step 2, image bar")
    root['one at a time']['d'] = co.Exec("echo step 3, image bar")
    return root

def path() -> co.Serial:
    root = co.Serial(image="foo")
    root['all together'] = co.Parallel()
    root['all together/a'] = co.Exec("echo step 1, image bar", image="bar")
    root['all together/b'] = co.Exec("echo step 1, image foo")
    root['one at a time'] = co.Serial(image="bar")
    root['one at a time/c'] = co.Exec("echo step 2, image bar")
    root['one at a time/d'] = co.Exec("echo step 3, image bar")
    return root

def context() -> co.Serial:
    with co.Serial(image=foo) as root:
        with co.Parallel(name="all together"):
            co.Exec("echo step 1, image bar", name="a", image=bar)
            co.Exec("echo step 1, image foo", name="b")
        with co.Serial(name="one at a time", image=bar) as two:
            co.Exec("echo step 2, image bar", name="c")
            co.Exec("echo step 3, image bar", name="d")
        return root

if __name__ == '__main__':
    co.main()
