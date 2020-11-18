import collections, conducto as co, json, re

############################################################
# Pipeline definition
############################################################
def run() -> co.Serial:
    "Download data from the US EIA, then visualize some datasets."
    with co.Serial(image=IMG, doc=co.util.magic_doc()) as output:
        # First download some data from the US Energy Information Administration.
        output["Download"] = co.Exec(DOWNLOAD_COMMAND)

        # Then make a few different visualizations of it.
        output["Display"] = co.Parallel()
        for dataset in DATASETS.keys():
            # Use co.Exec shorthand for calling native Python functions.
            # It calls `display(dataset)` in an Exec node. It's equal to:
            #   python pipeline.py display --dataset={dataset}
            output["Display"][dataset] = co.Exec(display, dataset)
    return output

############################################################
# Command to run
############################################################
def display(dataset):
    """
    Read in the downloaded data, extract the specified datasets, and plot them.
    """
    data_text = co.data.user.gets(DATA_PATH)
    all_data = [json.loads(line) for line in data_text.splitlines()]

    regex = DATASETS[dataset]
    subset_data = [
        d for d in all_data if "series_id" in d and re.search(regex, d["series_id"])
    ]

    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import pandas as pd
    import numpy as np

    # Create a pandas DataFrame with the data grouped by month of the year. This could
    # be implemented with vectorized pandas logic but this data is small enough not to
    # worry.
    data = {}
    for i, d in enumerate(subset_data):
        by_month = collections.defaultdict(list)
        for yyyymm, value in d["data"]:
            month = int(yyyymm[-2:])
            by_month[month].append(value)
        y = [np.mean(by_month[month]) for month in range(1, 13)]
        data[d["name"]] = y

    df = pd.DataFrame(data=data)
    df["Month"] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df.set_index("Month", inplace=True)

    # Graph each dataset as one line on a single plot.
    colors = [cm.viridis(z) for z in np.linspace(0, 0.99, len(subset_data))]
    for i, column in enumerate(df.columns):
        y = df[column].values
        plt.plot(y, label=column, color=colors[i])
    plt.title(f"{dataset}, average by month")
    plt.legend(loc="best", fontsize="x-small")

    # Save to disk, and then to co.data.pipeline
    filename = "/tmp/image.png"
    dataname = f"conducto/demo/weather_data/{dataset}.png"
    plt.savefig(filename)
    co.data.pipeline.put(dataname, filename)

    # Print out results as markdown
    print(f"""
<ConductoMarkdown>
![img]({co.data.pipeline.url(dataname)})

{df.transpose().round(2).to_markdown()}
</ConductoMarkdown>
    """)

############################################################
# Constants and globals
############################################################
DATA_PATH = "conducto/demo/weather_data/steo.txt"

DATASETS = {
    "Heating Degree Days": r"^STEO.ZWHD_[^_]*\.M$",
    "Cooling Degree Days": r"^STEO.ZWCD_[^_]*.M$",
    "Electricity Generation": r"^STEO.NGEPGEN_[^_]*\.M$",
}

IMG = co.Image(
    "python:3.8", copy_dir=".", reqs_py=["conducto", "pandas", "matplotlib", "tabulate"]
)

# Data is downloaded from the United States Energy Information Administration.
# https://www.eia.gov/opendata/bulkfiles.php
DOWNLOAD_COMMAND = f"""
echo "Downloading"
curl http://api.eia.gov/bulk/STEO.zip > steo.zip
unzip -cq steo.zip | conducto-data-user puts --name {DATA_PATH}
""".strip()

if __name__ == "__main__":
    co.main(default=run)
