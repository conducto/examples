# erastothenes

Three nodes, takes an int parameter, _n_
 - Use the Sieve of Erastothenes to calculate all primes up to _n_
 - Depending on the size of _n_, use either Bertrand's Postulate, or Nagura's Theorem to validate that the result is dense enough to consist of consecutive primes
 - Check that 2 is included

This example comes with a bug--the last test fails due to a problem in [sieve.py](sieve.py) .  Use the "live-debug" option to modify [sieve.py](sieve.py) and fix it.


### To Run

    python ./pipeline.py primes_up_to 200 --local

### Related

#### Concepts

- [Debugging](https://www.conducto.com/docs/basics/debugging)
- [Native Functions](https://www.conducto.com/docs/basics/native-functions)

#### API's

- [Image](https://conducto.com/api/docker.html#conducto.Image)
- [Node](https://conducto.com/api/nodes.html)
