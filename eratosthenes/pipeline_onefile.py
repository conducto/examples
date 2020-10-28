import conducto as co


def sieve(n: int):
    """
    Print all of the prime numbers less than n
    """

    primes = []
    for i in range(2, n):
        if all([i % p for p in primes]):
            primes.append(i)
            print(i)


# A pipeline which generates primes and runs some tests on the list
def primes_less_than(n: int) -> co.Serial:

    img = co.Image(copy_dir=".")

    with co.Serial(image=img) as root:
        root["find primes"] = co.Exec(sieve, n)

    return root


if __name__ == "__main__":
    co.main()
