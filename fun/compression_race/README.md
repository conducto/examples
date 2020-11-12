# Compression Race

This example performs the same workload three times.
  - five threads in one container
  - singly in five containers
  - sequentially in one container

The idea is that the user can tweak cpu availability to alter who wins the race.


### To Run With five jobs

    python ./pipeline.py --local

### To Run with 50 jobs

    python ./scale.py race 50 --cloud

### Related

#### Concepts

- [Controlling a Pipeline](https://www.conducto.com/docs/basics/controlling-a-pipeline)

#### API's

- [Image](https://conducto.com/api/docker.html#conducto.Image)
- [Node](https://conducto.com/api/nodes.html)
