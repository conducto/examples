#!/usr/bin/env python3
import sys

num = int(sys.argv[1])

# https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
primes = []
for i in range(3, num):
    if all([i % p for p in primes]):
        primes.append(i)

# write output
with open("primes", "w") as f:
    dots = False
    count = len(primes)
    for num, p in enumerate(primes):

        # write to file no matter what
        f.write(str(p) + "\n")

        if sys.stdout.isatty():
            # summarize output for humans
            if num < 3:
                print(p)
            elif count - num <= 3 and num > 3:
                print(p)
            else:
                if not dots:
                    print("...")
                    dots = True
        else:
            # full output for robots
            print(p)
