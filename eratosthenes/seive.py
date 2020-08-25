import sys

num = int(sys.argv[1])

# https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
primes = []
for i in range(3, num):
    if all([i % p for p in primes]):
        primes.append(i)

for p in primes:
    print(p)
