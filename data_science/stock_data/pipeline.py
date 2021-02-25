import conducto as co
import glob
import os


############################################################
# Main pipeline
############################################################
def main(start_date="20120101") -> co.Serial:
    """
    Build a volume-prediction model for SPY.US. Steps:
    * Download data from S3 to the /conducto/data drive.
    * Compute features in parallel.
    * Build 3 models in parallel to predict volume.
    * For each model, fit, then do a parallel backtest.
    * Once all backtests are complete, summarize the results.
    """
    path = "/conducto/data/pipeline"

    root = co.Serial(image=_get_image(), env={"PYTHONBREAKPOINT":"ipdb.set_trace"})
    root["Download"] = co.Exec(download_data, f"{path}/raw")

    # "Compute Features" should be parallelized at runtime, based on the actual
    # data downloaded in the previous step. Use co.Lazy to define and execute
    # this subtree.
    root["Compute Features"] = co.Lazy(
        make_compute_features_node,
        in_dir=f"{path}/raw",
        tmp_dir=f"{path}/feat/tmp",
        out_file=f"{path}/feat/merged.csv",
        start_date=start_date,
    )
    # Try three different model types
    root["Models"] = co.Parallel()
    for mdl in ["linear", "svm", "gradient_boost"]:
        # For each model, fit it, then backtest
        root["Models"][mdl] = fit_and_test = co.Serial()
        fit_and_test["Fit"] = co.Exec(
            fit,
            model_type=mdl,
            in_file=f"{path}/feat/merged.csv",
            out_file=f"{path}/fit/{mdl}",
        )
        fit_and_test["Backtest"] = co.Lazy(
            make_backtest_node,
            feature_dir=f"{path}/feat",
            model_file=f"{path}/fit/{mdl}",
            tmp_dir=f"{path}/results/tmp/{mdl}",
            out_file=f"{path}/results/{mdl}.csv",
        )

    # Analyze the results of the backtests and plot.
    root["Analyze"] = co.Exec(analyze, f"{path}/results")
    return root


############################################################
# Command line
############################################################
def download_data(out_dir):
    """
    Download data, then store it indexed by month.
    """

    os.makedirs(out_dir, exist_ok=True)

    df = _load_all_data()
    for yyyymm, subset in df.groupby(df.Date.str.replace("-", "").str[:6]):
        filename = f"{out_dir}/{yyyymm}.csv"
        print("Writing", filename)
        subset.to_csv(filename, index=False)


def make_compute_features_node(in_dir, tmp_dir, out_file, start_date="00000000") -> co.Serial:
    """
    Builds a tree for computing features. Parallelize over different months.
    """
    all_files = glob.glob(f"{in_dir}/*.csv")
    all_yyyymms = sorted({os.path.basename(f)[:-4] for f in all_files})

    os.makedirs(tmp_dir, exist_ok=True)

    # Skip the first month because we need 1 month of history to compute features
    all_yyyymms = all_yyyymms[1:]

    # Then subset to only the ones beyond the start date
    all_yyyymms = [yyyymm for yyyymm in all_yyyymms if yyyymm >= start_date[:6]]

    # Make output
    output = co.Serial()
    output["Parallelize"] = co.Parallel()
    for node, yyyymm in co.util.makeyyyymmnodes(output["Parallelize"], all_yyyymms):
        node[yyyymm] = co.Exec(compute_features, yyyymm, in_dir, tmp_dir)
    output["Merge"] = co.Exec(merge_data, tmp_dir, out_file)
    return output


def compute_features(yyyymm, in_dir, out_dir):
    """
    Compute features for a given month.
    """
    window_sizes = [1, 5, 10, 15]

    df = _load_raw_for_yyyymm(in_dir, yyyymm)

    # simple moving average for the last window days
    for window in window_sizes:
        df[f"{window}_avg"] = df["Vol"].rolling(window=window).mean().shift(1)

    df = df[df["curr"]]

    needed_cols = ["Date"] + [f"{window}_avg" for window in window_sizes]

    features = df[needed_cols]
    features["Y"] = df["Volume"]
    print(f"Writing features to {out_dir}/{yyyymm}.csv")
    print(features)
    features.to_csv(f"{out_dir}/{yyyymm}.csv", index=False)


def merge_data(tmp_dir, out_file):
    import pandas as pd

    all_files = glob.glob(f"{tmp_dir}/*.csv")
    df_list = [pd.read_csv(filename) for filename in sorted(all_files)]
    merged = pd.concat(df_list)
    # first month's data will have some nans because no previous month to fill moving average
    merged.dropna(axis=0, inplace=True)

    print(f"Writing merged training data to {out_file}")
    print(merged)
    merged.to_csv(out_file, index=False)


def fit(model_type, in_file, out_file):
    import pandas as pd

    if model_type == "linear":

        from sklearn.linear_model import LinearRegression

        model = LinearRegression()
    elif model_type == "svm":
        from sklearn.svm import SVR

        model = SVR()
    elif model_type == "xgb":
        from sklearn.ensemble import GradientBoostingRegressor

        model = GradientBoostingRegressor()
    else:
        raise Exception("Invalid model type: expected 'linear', 'svm', or 'xgb'")

    df = pd.read_csv(in_file)

    feature_cols = [f"{i}_avg" for i in [1, 5, 10, 15]]
    x, y = df.loc[:, feature_cols], df.Y

    from sklearn.model_selection import train_test_split

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, shuffle=False
    )

    clf = model.fit(x_train, y_train)
    print(f"{model_type} score: {clf.score(x_test, y_test)}")

    import pickle

    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    with open(out_file, "wb") as f:
        pickle.dump(clf, f)


def analyze(path):
    import matplotlib.pyplot as plt
    import pandas as pd

    # Set matplotlib to show its plots in Conducto
    co.nb.matplotlib_inline()

    os.makedirs(path, exist_ok=True)

    all_files = glob.glob(f"{path}/*.csv")
    for file in all_files:
        print(file)

        df = pd.read_csv(file)
        plt.plot(df["Date"], df["Score"])
        plt.show()


def backtest(model_file, yyyymm, tmp_dir):
    from sklearn.linear_model import LinearRegression
    from sklearn.svm import SVR
    from sklearn.ensemble import GradientBoostingRegressor
    import pandas as pd
    import pickle

    if yyyymm == "201709" and "linear" in model_file:
        raise ValueError("Malformed data detected")

    with open(model_file, "rb") as f:
        model = pickle.load(f)
    df = pd.read_csv(f"/conducto/data/pipeline/feat/tmp/{yyyymm}.csv")
    df.dropna(axis=0, inplace=True)
    feature_cols = [f"{i}_avg" for i in [1, 5, 10, 15]]
    x, y = df.loc[:, feature_cols], df.Y
    score = model.score(x, y)
    print(f"Score of {score} for {yyyymm} on model {model_file}")
    with open(f"{tmp_dir}/{yyyymm}.txt", "w") as f:
        f.write(str(score))


def merge_backtest(tmp_dir, out_file):

    all_files = sorted(glob.glob(f"{tmp_dir}/*.txt"))

    print(all_files)
    with open(out_file, "w") as f:
        f.write("Date,Score\n")
        f.write(
            "\n".join(
                f"{filename.split('/')[-1][:-4]},{score}"
                for filename, score in zip(
                    all_files, (float(open(i).read()) for i in all_files)
                )
            )
        )


def make_backtest_node(feature_dir, model_file, tmp_dir, out_file) -> co.Serial:
    """
    Builds a tree for computing features. Parallelize over different months.
    """

    os.makedirs(tmp_dir, exist_ok=True)

    all_files = glob.glob(f"{feature_dir}/tmp/*.csv")
    print(all_files)
    all_yyyymms = sorted({os.path.basename(f)[:-4] for f in all_files})

    # Make output
    output = co.Serial()
    output["Parallelize"] = co.Parallel()
    for node, yyyymm in co.util.makeyyyymmnodes(output["Parallelize"], all_yyyymms):
        node[yyyymm] = co.Exec(
            backtest, model_file=model_file, yyyymm=yyyymm, tmp_dir=tmp_dir
        )
    output["Merge"] = co.Exec(merge_backtest, tmp_dir, out_file)
    return output


############################################################
# Helper functions
############################################################
def _load_all_data():
    import boto3
    from botocore import UNSIGNED
    from botocore.client import Config
    import io
    import pandas as pd

    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    response = s3.get_object(Bucket="conducto-examples", Key="stock_data_spy.csv")
    contents = response["Body"].read()
    return pd.read_csv(io.BytesIO(contents))


def _load_raw_for_yyyymm(raw_dir, yyyymm):
    year, month = yyyymm[:4], yyyymm[4:]
    if int(month) == 1:
        last_year = int(year) - 1
        last_month = 12
    else:
        last_year = year
        last_month = int(month) - 1
    this = f"{year:>04}{month:>02}"
    last = f"{last_year:>04}{last_month:>02}"

    import pandas as pd

    last_df = pd.read_csv(f"{raw_dir}/{last}.csv")
    this_df = pd.read_csv(f"{raw_dir}/{this}.csv")

    last_df["curr"] = False
    this_df["curr"] = True

    return pd.concat([last_df, this_df])


def _get_image():
    return co.Image(
        "python:3.8-slim",
        copy_dir=".",
        reqs_py=["conducto", "boto3", "pandas", "sklearn", "matplotlib", "ipdb"],
    )


try:
    import IPython.core.crashhandler
except ImportError:
    pass
else:
    import traceback
    IPython.core.crashhandler.crash_handler_lite = traceback.print_exception


if __name__ == "__main__":
    co.main(default=main)
