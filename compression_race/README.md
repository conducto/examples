# Compression Race

This example performs the same workload twice.
  - five threads in one container
  - singly in five containers


The idea is that the user can tweak cpu allocation to alter who wins the race

### To Run

    python ./pipeline.py --local

### Related

#### Concepts

- [Controlling a Pipeline](https://www.conducto.com/docs/basics/image-handling#controlling-a-pipeline)

#### API's

- [Image](https://conducto.com/api/docker.html#conducto.Image)
- [Node](https://conducto.com/api/nodes.html)
