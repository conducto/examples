import conducto as co
from collections import namedtuple
import sys

# print all primes less than a given number
# and write them to a file called 'primes'
def seive(n: int):

    first_prime = 3 # this isn't true

    primes = []
    for i in range(2, n):
        if all([i % p for p in primes]):
            primes.append(i)

    with open('primes', 'w') as f:
        for p in primes:
            f.write(str(p) + '\n')

    # all primes go in the file, just the first and last 3 go in the output
    dots = False
    count = len(primes)
    for num, p in enumerate(primes):
        if num < 3:
            print(p)
        elif count - num <= 3 and num > 3:
            print(p)
        else:
            if not dots:
                print('...')
                dots = True

# read from a file called 'primes'
# exit nonzero if these aren't spaced like primes
def distrib(upper_bound: int):

    # load alledged primes
    primes = []
    with open('primes', 'r') as f:
        for numstr in f.readlines():
            primes.append(int(numstr))

    # based on their volume, select a distribution check
    FilterParam = namedtuple('FilterParam', 'n p')
    def bertrand(params):
        # valid for n >= 4, weaker claim
        # https://en.wikipedia.org/wiki/Bertrand%27s_postulate
        return params.n < params.p < (2*params.n - 2)

    def nagura(params):
        # valid for n >= 25, stronger claim
        # https://projecteuclid.org/download/pdf_1/euclid.pja/1195570997
        return params.n < params.p < (6/5)*params.n

    if upper_bound > 25:
        lower_bound = 25
        primes_between = nagura
        name = "Nagura's Theorem"

    elif upper_bound >= 4:
        lower_bound = 4
        primes_between = bertrand
        name = "Bertrand's Postulate"
    else:
        raise ValueError("No available distribution checks for n < 4")

    # fail if they are too sparse
    for n in range(lower_bound, max(primes)):
        if not any(filter(primes_between, [FilterParam(n, p) for p in primes])):
            print(f"{name} fails for n = {upper_bound}")
            sys.exit(2)
    print(f"{name} passes for n = {upper_bound}")

# A pipeline which generates primes and runs some tests on the list
def primes_less_than(n: int) -> co.Serial:


    img = co.Image(copy_dir=".")

    with co.Serial(same_container=co.SameContainer.NEW, image=img) as root:
        root["find primes"] = co.Exec(seive, n)
        if n >= 3:
            root["check distribution"] = co.Exec(distrib, n)
        root["is 2 included?"] = co.Exec("egrep '^2$' primes")

    return root


if __name__ == "__main__":
    co.main()

