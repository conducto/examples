import conducto as co
import json
from pathlib import Path

# commands.py and experiment.py are in the same folder as this file
from experiment import genomes, genes

download_img = co.Image(
    reqs_packages=["wget", "gzip"],
)

process_img = co.Image(
    image="ncbi/blast", copy_dir=".", reqs_py=["conducto", "biopython"]
)

analysis_img = co.Image(copy_dir=".", reqs_py=["conducto", "biopython", "pandas"])

data_dir = "/conducto/data/pipeline"


def download_file(source_url, target_path) -> co.Serial:
    "Returns a serial node which downloads a gzipped FASTA file"

    target_dir = Path(target_path).parent

    node = co.Serial()
    node["Download"] = co.Exec(
        f"mkdir -p {target_dir} && wget -O {target_path}.gz {source_url}"
    )
    node["Decompress"] = co.Exec(f"gunzip -c {target_path}.gz > {target_path}")

    return node


def process(target, genes, hits):
    """
    Search the target genome for the known genes
    """
    from Bio.Blast.Applications import (
        NcbiblastnCommandline as blastn,
        NcbimakeblastdbCommandline as makedb,
    )

    makedb(dbtype="nucl", input_file=target, out="tmp")()
    blastn(query=genes, outfmt=5, db="tmp", out=hits)()


def analyze(hits):
    """
    Print a list of genes found in more than one genome
    For more featureful analysis experience, use a notebook instead
    """

    import pandas as pd
    from Bio.Blast import NCBIXML

    hits = json.loads(hits)

    # parse blast output
    blast_records = {}
    for genome, file in hits.items():
        with open(file, "r") as f:
            blast_records[genome] = list(NCBIXML.parse(f))

    # aggregate hits by protein
    hits_by_protein = {}
    for genome, records in blast_records.items():
        for record in records:
            # exclude iterations that found nothing
            if record.alignments:
                try:
                    protein = record.query.split(" ")[0]
                except IndexError:
                    print(f"Couldn't find protein ID: {record.query}")
                hits_by_protein.setdefault(protein, set()).add(genome)

    # as a grid
    genomes_by_number = list(enumerate(sorted(hits.keys())))
    matrix = []
    for protein, found in hits_by_protein.items():
        # reference genes are from s_cerevisiae, expect them
        # include only hits in more than one genome
        if len(found) > 1:
            _hits = [0] * len(hits.keys())
            for i, genome in genomes_by_number:
                if genome in found:
                    _hits[i] = 1
            matrix.append([protein] + _hits)

    # as a data frame
    labels = ["protein"] + [x[1] for x in genomes_by_number]
    df = pd.DataFrame(matrix, columns=labels)
    print(df)


def main() -> co.Serial:

    with co.Serial() as root:

        with co.Parallel(name="Download", image=download_img) as download:

            # genomes
            for name, url, target_file in genomes(data_dir):
                download["genome: " + name] = download_file(url, target_file)

            # genes
            source_url, genes_file = genes(data_dir)
            download["genes: S288C"] = download_file(source_url, genes_file)

        hits = {}

        with co.Parallel(name="Process", image=process_img) as process_node:
            for name, _, target_file in genomes(data_dir):

                # keep track of outputs for analysis
                hits_file = f"{data_dir}/{name}.xml"
                hits[name] = hits_file

                process_node[name] = co.Exec(
                    process, target_file, genes_file, hits_file
                )

        root["Analyze"] = co.Exec(analyze, json.dumps(hits))
        root["Analyze"].image = analysis_img
        # root["Analyze"] = co.nb(something???)

    return root


if __name__ == "__main__":
    co.main(default=main)
