import conducto as co
import shelve
import json
import os
from pathlib import Path

data = Path("/conducto/data/pipeline")
share = str(data / "db")

# use these images
get_img = co.Image(reqs_packages=["wget", "gzip"])
bio_img = co.Image(
    image="ncbi/blast",
    copy_dir=".",
    reqs_py=["conducto", "biopython", "ipdb", "urlpath", "matplotlib"],
)

# from http://sgd-archive.yeastgenome.org/sequence/S288C_reference/orf_dna/
genes_url = "http://sgd-archive.yeastgenome.org/sequence/S288C_reference/orf_dna/orf_coding.fasta.gz"


def download_node(source_url) -> co.Serial:

    filename = Path(source_url).name  # foo.fna.gz
    in_path = data / filename  # /cdp/foo.fna.gz
    out_path = data / Path(filename).stem  # /cdp/foo.fna

    node = co.Serial(image=get_img)
    node["Download"] = co.Exec(f"wget -O {in_path} {source_url}")
    node["Decompress"] = co.Exec(f"gunzip -c {in_path} > {out_path}")

    node.on_error(co.callback.retry(3))

    return node, out_path


def find_yeasts() -> co.Serial:

    # these aren't pipeline-launch-time dependencies
    # they are only needed by the "Get Gene Data" node
    # so they're imported only where needed
    from Bio import Entrez
    from pprint import pprint
    from urlpath import URL
    import ipdb

    # configure these in conducto user profile
    Entrez.email = os.environ["NCBI_EMAIL"]
    Entrez.api_key = os.environ["NCBI_API_KEY"]

    # search query: "yeast" -> genomes
    handle = Entrez.esearch(db="genome", term="yeast", retmode="xml", retmax="200")
    genome_ids = ",".join(Entrez.read(handle)["IdList"])

    # iterate through genomes and gather results
    genomes = {}
    download = co.Parallel(image=get_img)
    handle = Entrez.esummary(db="genome", id=genome_ids)
    for genome in Entrez.parse(handle):

        try:
            # genome -> assembly
            assy_id = genome["AssemblyID"]
            handle = Entrez.esummary(db="assembly", id=assy_id)
            assembly = Entrez.read(handle)

            doc = assembly["DocumentSummarySet"]["DocumentSummary"][0]
            assy_name = doc["AssemblyName"]
            ncbi_ref = doc["AssemblyAccession"]
            org_name = genome["Organism_Name"]
            desc = genome["DefLine"]

            # assembly -> nucleotides (ftp)
            url = URL(doc["FtpPath_RefSeq"] or doc['FtpPath_GenBank'])
            file = url.name + "_genomic.fna.gz"
            ftp = url / file

            #if 'Brett' in org_name:
            #    ipdb.set_trace()

            node, path = download_node(ftp)
            download[org_name] = node

            # stash genome metadata
            target = {"name": org_name, "desc": desc, "file": path, "ref": ncbi_ref}
            genomes[org_name] = target
            print(f"genome: {json.dumps(target, default=str)}")

        except IndexError:
            continue  # skip genomes that don't have assemblies

        except Entrez.Parser.ValidationError:
            continue  # skip genomes that got scrozzled in transit

    # save genomes for later
    with shelve.open(share) as db:
        db["genomes"] = genomes

    # also download a list of reference genes
    reference_genes, path = download_node(genes_url)
    download["S288C"] = reference_genes
    with shelve.open(share) as db:
        db["genes"] = {"file": path}

    # tell the rest of the pipeline how many download nodes to add
    return download


def main() -> co.Serial:
    with co.Serial(image=bio_img) as node:
        node["Get Gene Data"] = co.Lazy(find_yeasts)
    return node


if __name__ == "__main__":
    co.main(default=main)
