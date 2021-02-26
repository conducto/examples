import conducto as co
from pathlib import Path

# six yeasts: three liked by brewers, three chosen arbitrarily
_genomes = {
    "s_cerevisiae": {
        "gist": "https://en.wikipedia.org/wiki/Saccharomyces_cerevisiae",
        "url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/146/045/GCF_000146045.2_R64/GCF_000146045.2_R64_genomic.fna.gz",
    },
    "b_bruxellensis": {
        "gist": "https://en.wikipedia.org/wiki/Brettanomyces",
        "url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/011/074/885/GCA_011074885.2_ASM1107488v2/GCA_011074885.2_ASM1107488v2_genomic.fna.gz",
    },
    "z_kombuchaensis": {
        "gist": "https://academic.oup.com/femsyr/article/1/2/133/570110",
        "url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/003/705/955/GCA_003705955.1_ASM370595v1/GCA_003705955.1_ASM370595v1_genomic.fna.gz",
    },
    "d_albidus": {
        "gist": "https://en.wikipedia.org/wiki/Dipodascus",
        "url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/003/707/475/GCA_003707475.1_ASM370747v1/GCA_003707475.1_ASM370747v1_genomic.fna.gz",
    },
    "c_parapsilosos": {
        "gist": "https://en.wikipedia.org/wiki/Candida_parapsilosis",
        "url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/182/765/GCF_000182765.1_ASM18276v2/GCF_000182765.1_ASM18276v2_genomic.fna.gz",
    },
    "s_bombicola": {
        "gist": "https://en.wikipedia.org/wiki/Starmerella",
        "url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/001/599/315/GCA_001599315.1_JCM_9596_assembly_v001/GCA_001599315.1_JCM_9596_assembly_v001_genomic.fna.gz",
    },
}

def genomes(data_dir):
    for name, ref in _genomes.items():
        source_url = ref["url"]
        target_file = Path(data_dir) / ("genome_" + name + ".fna")
        yield (name, source_url, target_file)


# a list of the genes in a well studied strain of saccharomyces_cerevisiae
_reference = {
    "gist" : "https://www.yeastgenome.org/strain/S000203483",
    "source" : "https://www.yeastgenome.org/search?q=&category=download&status=Active",
    "readme_url" : "https://sgd-prod-upload.s3.amazonaws.com/S000208181/orf_dna.README",
    "url" : "https://sgd-prod-upload.s3.amazonaws.com/S000208654/orf_coding.20150113.fasta.gz",
}

def genes(data_dir):
    source_url = _reference["url"]
    target_file = Path(data_dir) / "genes.fna"
    return source_url, target_file
