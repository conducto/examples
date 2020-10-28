import conducto as co
from collections import namedtuple
import sys


def primes_less_than(n) -> co.Serial:
    n = int(n)
    img = co.Image(copy_dir=".")

    with co.Serial(same_container=co.SameContainer.NEW, image=img) as root:
        root["find primes"] = co.Exec(f"python sieve.py {n}")
        if n >= 3:
            root["check distribution"] = co.Exec(f"cat primes | python check.py {n}")
        root["is 2 included?"] = co.Exec("egrep '^2$' primes")

    return root


def primes_less_than_fixed(n) -> co.Serial:

    # run the fixed version of the script
    root = primes_less_than(n)
    root.children["find primes"].command = f"python sieve_fixed.py {n}"
    return root


if __name__ == "__main__":
    co.main()
