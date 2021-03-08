import json
import conducto as co

from my_experiment import process_data, notebook_pkgs


def root() -> co.Serial:
    "Returns the root of a pipeline tree"

    # Children of a Serial node run one after another.
    root = co.Serial()
    root["Download"] = download()
    root["Process"] = process()
    root["Analyze"] = analyze()

    return root


# a place to persist data across nodes
data_dir = "/conducto/data/pipeline"


def download() -> co.Exec:
    "Returns a node to get data from conducto.com"

    # Image objects define environments.
    img = co.Image(install_packages=["wget"])

    # Exec nodes run commands or call functions in those environments.
    return co.Exec(
        f"wget -NcP {data_dir} http://192.168.90.13:8887/genedata.zip",
        #f"wget -NcP {data_dir} https://conducto.com/demo/genedata.zip",
        image=img,
    )


# "Process" and "Analyze" share an image.  To build it:
# - start with a premade image from dockerhub
# - include the local directory so we can reference its other files
# - pip install their dependencies
bio_img = co.Image("ncbi/blast",
                   copy_dir=".",
                   install_pip=["pandas", "biopython"] + notebook_pkgs)


def process() -> co.Parallel:
    "Returns a node to process the data in parallel"

    # This node makes three parallel calls to my_experiment.process_data(),
    # each time with different parameters.
    node = co.Parallel(image=bio_img)
    for i in range(3):
        node[str(i + 1)] = co.Exec(process_data, dataset=i, data_dir=data_dir)

    return node


def analyze() -> co.Exec:
    "Returns a node to help understand the processed results"

    # Run this node to completion and view its output like a report,
    # or leave it running and interact with the data notebook-style.

    node = co.Notebook("analyze.ipynb", dir=data_dir, datasets=json.dumps([1, 2, 3]))
    node.image = bio_img

    # Give it some extra resources for easy exploration
    node.cpu = 4
    node.mem = 32

    return node


# use `python pipeline.py --local` to launch this pipeline locally
#  or `python pipeline.py --cloud` to launch it in the cloud
if __name__ == "__main__":
    co.main(default=root)

# The commands above will print a link and open a browser.  From there
# you can interact with the pipeline.

