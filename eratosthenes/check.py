#!/usr/bin/env python3
from collections import namedtuple
import sys, select

# exit nonzero if these aren't spaced like primes
def distrib(upper_bound):

    # load alledged primes
    primes = []

    for numstr in sys.stdin.readlines():
        primes.append(int(numstr))

    # based on their volume, select a distribution check
    FilterParam = namedtuple("FilterParam", "n p")

    def bertrand(params):
        # valid for n >= 4, weaker claim
        # https://en.wikipedia.org/wiki/Bertrand%27s_postulate
        return params.n < params.p < (2 * params.n - 2)

    def nagura(params):
        # valid for n >= 25, stronger claim
        # https://projecteuclid.org/download/pdf_1/euclid.pja/1195570997
        return params.n < params.p < (6 / 5) * params.n

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


if __name__ == "__main__":
    distrib(int(sys.argv[1]))
