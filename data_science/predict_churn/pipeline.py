"""
Make churn prediction model based on input data.

Run this with `python pipeline.py --local --run`.

Adapted from https://www.kaggle.com/kmalit/bank-customer-churn-prediction.
"""
import conducto as co
import math
import os

IMG = co.Image(
    "python:3.8",
    copy_dir=".",
    reqs_py=["numpy", "pandas", "matplotlib", "xgboost", "seaborn", "conducto",
             "sklearn", "tabulate", "tqdm"],
    reqs_packages=["figlet"],
)
R_IMG = co.Image(dockerfile="docker/Dockerfile.r", copy_dir=".")

CUST = "data/customer_data.csv"
TRNS = "data/transaction_data.csv"

MODELS = ["logistic", "rf", "xgb"]

INTRO = "_Conducto_ for Data Science"


################################################################################
# Pipeline
################################################################################
def main() -> co.Serial:
    """
    A sample pipeline to predict customer churn:
    * Load in customer and transaction data
    * Join them
    * Compute features
    * Fit and backtest several different ML models
    * Analyze all the results and pick the best one.
    """
    output = co.Serial(image=IMG, doc=co.util.magic_doc())
    output["Intro"] = co.Exec(f"figlet '{INTRO}'")

    # Load data sources into temporary storage with the command-line
    # interface to [co.data](/api/data).
    output["LoadData"] = co.Parallel(doc=co.util.magic_doc(comment=True))
    output["LoadData/Customer"] = co.Exec(
        f"conducto-data-pipeline put /raw/cust {co.relpath(CUST)}"
    )
    output["LoadData/Transaction"] = co.Exec(
        f"conducto-data-pipeline put /raw/trns {co.relpath(TRNS)}"
    )

    # Join customer data (`cust`) with transaction data (`trns`).
    #
    # The data could be large, so we split this join up into smaller chunks. We
    # can't figure out the chunks, however, until after `/LoadData` has run.
    # Therefore the `/Join/Generate` step analyzes the data and creates nodes,
    # then `/Join/Execute` runs them. See
    # [co.Lazy](/api/pipelines/#lazy-pipeline-creation) for more details.
    output["Join"] = co.Lazy(join,
        "/raw/cust", "/raw/trns", out="/joined", tmp="/tmp/join", on="CustomerId"
    )
    output["Join"].doc = co.util.magic_doc(comment=True)

    # After merging customer records with their transaction history, we
    # prepare the data for input into a machine learning model.
    output["ComputeFeatures"] = co.Exec(
        "python commands.py compute_features /joined /features",
        doc=co.util.magic_doc(comment=True)
    )

    # Fit & backtest machine learning models in parallel
    output["Models"] = co.Parallel(doc=co.util.magic_doc(comment=True))
    for md in MODELS:
        output["Models"][md] = co.Serial()
        output["Models"][md]["Fit"] = co.Exec(
            f"python commands.py fit {md} /features /models/{md}"
        )
        output["Models"][md]["Backtest"] = co.Exec(
            f"python commands.py backtest /features /models/{md} /results/{md}"
        )

    # Analyze the backtests to find the best model. Use R, because
    # commands can be from any language, not just Python.
    output["Analyze"] = co.Exec(
        "Rscript analyze.R /results", image=R_IMG,
        doc=co.util.magic_doc(comment=True),
    )

    # We run the Analyze step in R to emphasize that commands can be in any
    # language. If you work exclusively in Python, command that out and run
    # this instead:
    # output["Analyze"] = co.Exec("python commands.py analyze /results")

    return output


def join(left, right, out, tmp, on, chunk_size=5000) -> co.Serial:
    """
    Inner join the given DataFrames in parallel, then merge them.

    * `left` - path in `co.data.pipeline` to the left DataFrom to join.
    * `right` - path in `co.data.pipeline` to the right DataFrame to join.
    * `out` - path in `co.data.pipeline` to write the result.
    * `tmp` - path in `co.data.pipeline` to write temporary data
    * `on` - column to join on
    * `chunk_size` - how many rows to include in each parallel chunk. 5000 is an
      artificially low number so that this demo can show parallelism. In real
      usage you would adjust this for your I/O and memory availability.
    """
    df_l = _read_dataframe(left)
    df_r = _read_dataframe(right)

    output = co.Serial()

    # Step 1, join blocks in parallel
    output["Parallelize"] = co.Parallel()

    base_l = os.path.basename(left)
    base_r = os.path.basename(right)
    for start_l, end_l in _batch(df_l[on], chunk_size):
        name_l = f"{base_l}:{start_l}-{end_l}"
        output["Parallelize"][name_l] = node1 = co.Parallel()

        for start_r, end_r in _batch(df_r[on], chunk_size):
            name_r = f"{base_r}:{start_r}-{end_r}"
            tmp_name = f"{tmp}/{base_l}:{start_l}-{end_l}_{base_r}:{start_r}-{end_r}"
            node1[name_r] = co.Exec(
                do_join, left, right, tmp_name, on, start_l, end_l, start_r, end_r
            )

    # Step 2, merge the results
    output["Merge"] = co.Exec(do_concat, tmp, out)

    return output


################################################################################
# Implementation
################################################################################
def do_join(left, right, out, on, start_idx_l: int, end_idx_l: int, start_idx_r: int, end_idx_r: int):
    """
    Do one portion of a parallel merge: load the left and right DataFrames, subset
    to the given indices, and join.
    """
    df_l = _read_dataframe(left).iloc[start_idx_l:end_idx_l]
    df_r = _read_dataframe(right).iloc[start_idx_r:end_idx_r]
    out_df = df_l.merge(df_r, on=on)
    _write_dataframe(out_df, out)


def do_concat(input: str, output: str):
    """
    Concatenate all DataFrames at `input` and save them to `out`.
    """
    import pandas as pd
    import tqdm
    in_paths = co.data.pipeline.list(input)
    in_dfs = [_read_dataframe(path) for path in tqdm.tqdm(in_paths)]
    out_df = pd.concat(in_dfs)
    _write_dataframe(out_df, output)


def _batch(series, chunk_size):
    """
    Helper to split up the series into even-sized chunks of under the given size.
    """
    num_chunks = math.ceil(len(series) / chunk_size)
    chunk_size = int(math.ceil(len(series) / num_chunks))
    for start in range(0, len(series), chunk_size):
        end = min(start + chunk_size, len(series))
        yield start, end


def _read_dataframe(path):
    """
    Read the pandas.DataFrame stored in co.data.pipeline.
    """
    import pandas as pd
    import io
    data = co.data.pipeline.gets(path)
    return pd.read_csv(io.BytesIO(data))


def _write_dataframe(df, path):
    """
    Write the pandas.DataFrame to co.data.pipeline.
    """
    data = df.to_csv()
    co.data.pipeline.puts(path, data.encode())


if __name__ == "__main__":
    co.main(default=main)