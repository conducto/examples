import conducto as co


def main() -> co.Serial:
    raw = "/conducto/data/user/examples/genomics"
    dir = "/conducto/data/pipeline"
    with co.Serial(image=get_image(), env=ENV) as root:
        root["Download"] = co.Exec(GET_DATA_CMD.format(raw))
        root["Preprocess"] = co.Exec(f"python commands.py preprocess {raw} {dir}/processed.h5ad")
        root["PCA"] = co.Exec(f"python commands.py pca {dir}/processed.h5ad {dir}/pca.h5ad")
        root["Neighborhood"] = co.Exec(f"python commands.py pca {dir}/pca.h5ad {dir}/neighborhood.h5ad")
        root["Markers"] = co.Parallel()
        for method in "t-test", "wilcoxon", "logreg":
            root["Markers"][method] = co.Exec(f"python commands.py marker {method} {dir}/neighborhood.h5ad")
    return root


def get_image():
    return co.Image(
        "python:3.8-slim",
        copy_dir=".",
        reqs_packages=["wget"],
        reqs_py=["conducto", "numpy", "pandas", "scanpy", "ipdb"]
    )


ENV = {"PYTHONBREAKPOINT":"ipdb.set_trace"}

GET_DATA_CMD = """
set -ex

DIR={}
if [[ ! -d "$DIR/genes.tsv" ]]; then 
    cd /tmp
    wget http://cf.10xgenomics.com/samples/cell-exp/1.1.0/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz -O data.tar.gz
    tar -xzvf data.tar.gz
    mkdir -p $DIR
    cp -prv filtered_gene_bc_matrices/hg19/* $DIR
else
    echo "Data already downloaded"
    find $DIR
fi
"""


if __name__ == "__main__":
    co.main(default=main)