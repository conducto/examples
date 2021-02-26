# Saccromyces Cerevisiae

This pipeline uses [Blast+](https://blast.ncbi.nlm.nih.gov/Blast.cgi) to find alignments of genes from [yeastgenome.org](https://www.yeastgenome.org/) against genomes of less-commonly-studied yeast species (genomes from [NCBI](https://www.ncbi.nlm.nih.gov/genome)).

It installs [biopython](https://biopython.org/docs/dev/api/Bio.Blast.Applications.html) into the [ncbi/blast](https://hub.docker.com/r/ncbi/blast) docker image and executes the search in parallel.

This parallelism is only about twice as fast as serial execution, but there may be similar workloads where this kind of parallelism makes a big difference.

### To Run

    python pipeline.py --local --run
