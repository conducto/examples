# Container Reuse

This example uses one increments a number in a file in one node and checks to see if it was incremented in the next node.
Altering co.SameContainer will affect whether the updated value makes it to the next node.


### A Potentially Surprising Result

    python ./increment.py default_serial --local --run

### Isolate Container Reuse

    python ./increment.py fixed_serial --local --run

### Isolate Further

    python ./increment.py isolated_serial --local --run

### Escape a Reuse Domain

    python ./increment.py escaped_serial --local --run

### Run in Parallel With _n_ jobs

(where n = 5)

    python ./increment.py parallel 5 --local --run

### Related

#### Concepts

- [Same Container](https://www.conducto.com/docs/basics/same-container)

#### API's

- [Node](https://conducto.com/api/nodes.html)
