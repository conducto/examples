# fortune_messy

This example creates a pipeline with one node for every day of the current month.
It's "messy" because rather than encapsulating its dependencies in containers, it depends on packages on the user's local system.
It's the precursor to "fortune_clean" which will use a Lazy node to work around this problem.

### To Run

Use your system's package manager to install `fortune`

Python dependencies

    pip install -r requirements.txt
    python ./pipeline.py --local

### Concepts

- [controlling-a-pipeline](https://conducto.com/docs/basics/controlling-a-pipeline)
- [--local and --cloud](https://conducto.com/docs/basics/local-vs-cloud)
