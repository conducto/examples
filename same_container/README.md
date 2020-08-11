# Same Container

This example uses one increments a number in a file in one node and checks to see if it was incremented in the next node.
Altering co.SameContainer will affect whether the updated value makes it to the next node.


### To Run With 3 jobs

    python ./increment.py serial --local --run

### To Run With n jobs

(where n = 5)

    python ./increment.py parallel 5 --local --run

### Related

#### Concepts

- [Same Container](https://www.conducto.com/docs/basics/same-container)

#### API's

- [Node](https://conducto.com/api/nodes.html)
