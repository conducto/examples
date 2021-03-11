from pathlib import Path
import shelve
import shutil

notebook_pkgs = ["conducto", "jupyterlab", "papermill", "watchdog", "ipdb", "black"]

genome_names = [
    "s_cerevisiae",
    "b_bruxellensis",
    "z_kombuchaensis",
    "d_albidus",
    "c_parapsilosos",
    "s_bombicola",
]

gene_files = {
    "S288C": "orf_coding_all.20150113.fasta",
}

genome_files = {
    "s_cerevisiae": "GCF_000146045.2_R64_genomic.fna",
    "b_bruxellensis": "GCA_011074885.2_ASM1107488v2_genomic.fna",
    "z_kombuchaensis": "GCA_003705955.1_ASM370595v1_genomic.fna",
    "d_albidus": "GCA_003707475.1_ASM370747v1_genomic.fna",
    "c_parapsilosos": "GCF_000182765.1_ASM18276v2_genomic.fn",
    "s_bombicola": "GCA_001599315.1_JCM_9596_assembly_v001_genomic.fna",
}

zip_file = "genedata.zip"


def _resolve_file_pair(dataset, queries, data_dir_path):
    """
    Accept dataset references as numbers or genome names.  This lets
    callers be generic (when discussing Conducto) or transparent (when
    discussing bioinformatics).
    """

    # dataset = "s_serevisiae" #  or whichever key from the above dict
    if not dataset in genome_files:
        try:
            dataset = genome_names[int(dataset)]
        except IndexError as err:
            msg = f"Unknown dataset reference: {dataset}.  Try these:"
            for i, name in enumerate(genome_names):
                msg += f"\n\t{i}: {name}"
            err.message = msg
            raise

    genome_name = dataset
    genome_file = data_dir_path / genome_files[genome_name]
    genes_file = data_dir_path / gene_files[queries]

    return genome_name, genome_file, genes_file


def process_data(dataset, queries="S288C", data_dir=Path("/conducto/data/pipeline/")):
    """
    Build a BLAST database for this genome, then search it for known genes.
    Store output as seralized pandas dataframe in {datadir}/{genome_name}.pkl
    """

    # The pipeline definition references--but doesn't call--this function.
    # Putting the imports here avoids adding dependencies to the definition.
    import zipfile
    import pandas as pd
    from Bio.Blast.Applications import (
        NcbiblastnCommandline as blastn,
        NcbimakeblastdbCommandline as makedb,
    )
    from Bio.Blast import NCBIXML, Record as NCBIRecord

    # resolve file paths
    data_dir = Path(data_dir)
    genome_name, genome_file, genes_file = _resolve_file_pair(
        dataset, queries, data_dir
    )

    # unzip payload if not already
    if not (genome_file.exists() and genes_file.exists()):
        shutil.unpack_archive(data_dir / zip_file, data_dir)
        print(f"unzipped {zip_file} into {data_dir}")

    print(f"searching {genome_file} for genes found in {genes_file}")

    # search for alignments
    alignments_file = f"{genome_name}.xml"
    makedb(dbtype="nucl", input_file=genome_file, out=genome_name)()
    blastn(query=genes_file, outfmt=5, db=genome_name, out=alignments_file)()

    # store interim result somewhere persistent
    shutil.copy(alignments_file, f"{data_dir / alignments_file}")

    # aggregate results
    rows = []
    with open(alignments_file, "r") as f:
        for record in NCBIXML.parse(f):
            if record.alignments:

                # index by protein name, tolerate parse errors
                protein_err_ct = 0
                try:
                    protein = record.query.split(" ")[0]
                    protein_desc = record.query
                except IndexError:
                    protein_err_ct += 1
                    print(f"Couldn't find protein ID: {record.query}")
                    protein = protein_desc = f"err{err_ct}: {record.query[:35]}"

                # extract each alignment found
                gene_err_ct = 0
                for alignment in record.alignments:
                    try:
                        parts = alignment.title.split(" ")
                        species = " ".join(parts[2:3])
                        genome_loc = " ".join(parts[4:])
                    except IndexError:
                        gene_arr_ct += 1
                        print(f"Couldn't find species info: {alignment.title}")
                        species = genome_loc = f"err{err_ct}: {record.query[:35]}"

                    for hsp in alignment.hsps:
                        locstr = f"{hsp.sbjct_start},{hsp.sbjct_end}"
                        score = hsp.score
                        desc = str(hsp)

                        # something unique for each one of these
                        key = "-".join([protein, species, alignment.title, locstr])

                        rows.append(
                            [
                                species,
                                genome_loc + ":" + locstr,
                                protein,
                                protein_desc,
                                score,
                                queries,
                                genes_file,
                                genome_name,
                                genome_file,
                                record,
                                hsp,
                                key,
                            ]
                        )

    df = pd.DataFrame(
        rows,
        columns=[
            "species",
            "locus",
            "protein",
            "protein_desc",
            "score",
            "genes_tag",
            "genes_file",
            "genome_name",
            "genome_file",
            "record",
            "hsp",
            "key",
        ],
    )

    print("prepared data frame:")
    print(df)

    # save results for later analysis
    shelf_fname = str(data_dir / genome_name)
    with shelve.open(shelf_fname) as shelf:
        shelf['frame'] = df
    print(f"wrote {shelf_fname}")
