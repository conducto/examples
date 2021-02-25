"""
### Data science pipeline to build customer churn prediction model.
Adapted from https://www.kaggle.com/kmalit/bank-customer-churn-prediction.
"""
import conducto as co


########################################################################
# Pipeline
########################################################################
def main() -> co.Serial:
    with co.Serial(image=get_image(), doc=ROOT_DOC) as output:
        output["Intro"] = co.Exec(f"figlet '_Conducto_ for Data Science'")

        with co.Parallel(name="LoadData", doc=LOAD_DOC) as load:
            load["Customer"] = co.Exec(PUT_CUSTOMER_DATA_CMD)
            load["Transaction"] = co.Exec(PUT_TRANSACTION_DATA_CMD)

        output["Join"] = co.Lazy(join_customer_transaction_data)
        output["Join"].doc = JOIN_DOC

        output["ComputeFeatures"] = co.Exec(COMPUTE_CMD, doc=COMPUTE_DOC)

        with co.Parallel(name="Models", doc=MODELS_DOC):
            for md in ["logistic", "random_forest", "gradient_boost"]:
                with co.Serial(name=md) as fit_and_test:
                    fit_and_test["Fit"] = co.Exec(FIT_CMD.format(md=md))
                    fit_and_test["Backtest"] = co.Exec(BACKTEST_CMD.format(md=md))

        output["Analyze"] = co.Exec(ANALYZE_CMD, doc=ANALYZE_DOC)

    return output


def join_customer_transaction_data() -> co.Serial:
    return join(
        "/conducto/data/pipeline/raw/cust",
        "/conducto/data/pipeline/raw/trns",
        out="/conducto/data/pipeline/joined",
        tmp="/conducto/data/pipeline/tmp/join",
        on="CustomerId"
    )


def join(left, right, out, tmp, on, chunk_size=5000) -> co.Serial:
    """
    Inner join the given DataFrames in parallel, then merge them.

    * `left` - path to the left DataFrame to join.
    * `right` - path to the right DataFrame to join.
    * `out` - path to write the result.
    * `tmp` - path to write temporary data
    * `on` - column to join on
    * `chunk_size` - how many rows to include in each parallel chunk. 5000 is an
      artificially low number so that this demo can show parallelism. In real
      usage you would adjust this for your I/O and memory availability.
    """
    import os
    import pandas as pd
    base_l = os.path.basename(left)
    base_r = os.path.basename(right)
    df_l = pd.read_csv(left)
    df_r = pd.read_csv(right)

    with co.Serial() as output:
        # Step 1, join blocks in parallel
        with co.Parallel(name="Parallelize") as parallelize:
            for start_l, end_l in _batch(df_l[on], chunk_size):
                name_l = f"{base_l}:{start_l}-{end_l}"
                parallelize[name_l] = node = co.Parallel()

                for start_r, end_r in _batch(df_r[on], chunk_size):
                    name_r = f"{base_r}:{start_r}-{end_r}"
                    tmp_name = f"{tmp}/{base_l}:{start_l}-{end_l}_{base_r}:{start_r}-{end_r}"
                    node[name_r] = co.Exec(
                        do_join, left, right, tmp_name, on, start_l, end_l, start_r, end_r
                    )

        # Step 2, merge the results
        output["Merge"] = co.Exec(do_concat, tmp, out)

    return output


def get_image():
    return co.Image(dockerfile="./Dockerfile", copy_dir=".")


########################################################################
# Commands
########################################################################
PUT_CUSTOMER_DATA_CMD = """
mkdir -p /conducto/data/pipeline/raw && cp ./data/customer_data.csv /conducto/data/pipeline/raw/cust
"""

PUT_TRANSACTION_DATA_CMD = """
mkdir -p /conducto/data/pipeline/raw && cp ./data/transaction_data.csv /conducto/data/pipeline/raw/trns
"""

COMPUTE_CMD = """
python commands.py compute_features /conducto/data/pipeline/joined /conducto/data/pipeline/features
"""

FIT_CMD = """
python commands.py fit {md} /conducto/data/pipeline/features /conducto/data/pipeline/models/{md}
"""

BACKTEST_CMD = """
python commands.py backtest /conducto/data/pipeline/features /conducto/data/pipeline/models/{md} /conducto/data/pipeline/results/{md}
"""

ANALYZE_CMD = """
Rscript analyze.R /conducto/data/pipeline/results
"""

########################################################################
# Native python functions called by pipeline.
########################################################################
def do_join(left, right, out, on, start_idx_l: int, end_idx_l: int, start_idx_r: int, end_idx_r: int):
    """
    Do one portion of a parallel merge: load the left and right DataFrames, subset
    to the given indices, and join.
    """
    import os
    import pandas as pd

    if start_idx_l == 0 and start_idx_r == 30653:
        raise ValueError("Malformed data detected")

    df_l = pd.read_csv(left).iloc[start_idx_l:end_idx_l]
    df_r = pd.read_csv(right).iloc[start_idx_r:end_idx_r]
    out_df = df_l.merge(df_r, on=on)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    out_df.to_csv(out)


def do_concat(input: str, output: str):
    """
    Concatenate all DataFrames at `input` and save them to `out`.
    """
    import os
    import pandas as pd
    import tqdm
    in_paths = os.listdir(input)
    in_dfs = [pd.read_csv(os.path.join(input, path)) for path in tqdm.tqdm(in_paths)]
    out_df = pd.concat(in_dfs)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    out_df.to_csv(output)


def _batch(series, chunk_size):
    """
    Helper to split up the series into even-sized chunks of under the given size.
    """
    import math
    num_chunks = math.ceil(len(series) / chunk_size)
    chunk_size = int(math.ceil(len(series) / num_chunks))
    for start in range(0, len(series), chunk_size):
        end = min(start + chunk_size, len(series))
        yield start, end


########################################################################
# Docs
########################################################################

ROOT_DOC = """
A sample pipeline to predict customer churn:
* Load in customer and transaction data
* Join them
* Compute features
* Fit and backtest several different ML models
* Analyze all the results and pick the best one.
"""

LOAD_DOC = """
Load data sources into the [/conducto/data/pipeline file system](/docs/basics/data).
Alternatively, you could load data into S3 or some other storage solution.
"""

JOIN_DOC = """
Join customer data (`cust`) with transaction data (`trns`).

The data could be large, so we split this join up into smaller chunks. We
can't figure out the chunks, however, until after `/LoadData` has run.
Therefore the `/Join/Generate` step analyzes the data and creates nodes,
then `/Join/Execute` runs them. See
[co.Lazy](/api/pipelines/#lazy-pipeline-creation) for more details.
"""

COMPUTE_DOC = """
After merging customer records with their transaction history, we
prepare the data for input into a machine learning model.
"""

MODELS_DOC = """
Fit and backtest machine learning models in parallel.
"""

ANALYZE_DOC = """
Analyze the backtests to find the best model. Use R, because
commands can be from any language, not just Python.
"""

if __name__ == "__main__":
    co.Image.share_directory("predict_churn", ".")
    co.main(default=main)
