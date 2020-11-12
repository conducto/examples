import sys

num = int(sys.argv[1])

# https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
primes = []
for i in range(2, num):
    if all([i % p for p in primes]):
        primes.append(i)

# all primes go in the file, just the first and last 3 go in the output
first = 3
last = 3
dots = False
count = len(primes)
with open("primes", "w") as f:
    for num, p in enumerate(primes):

        # add to file
        f.write(str(p) + "\n")

        if num < 3:
            print(p)
        elif count - num <= 3 and num > 3:
            print(p)
        else:
            if not dots:
                print("...")
                dots = True
