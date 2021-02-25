import conducto as co

try:
    from . import commands
except ImportError:
    import commands


DATA_ROOT = "/conducto/data/user/yt8m"
COVS_ROOT = "/conducto/data/pipeline/covs"
MERGED_TMP = "/conducto/data/pipeline/merged/tmp"
MERGED_FILE = "/conducto/data/pipeline/merged/output.pkl.gzip"
MODEL_DIR = "/conducto/data/pipeline/models"
BACKTEST_ROOT = "/conducto/data/pipeline/backtests"


def pipeline(num_shards=500, max_shard=3) -> co.Serial:
    root = co.Serial()
    # Download raw data
    root["Download"] = download_node(DATA_ROOT, num_shards, max_shard)

    # Compute covariance matrices. Use co.Lazy to generate tree
    #   (map) Compute covs in parallel, one for each tfrecord file (implemented, need tree)
    root["Compute covariance matrices"] = co.Lazy(
        compute_covs_node,
        in_glob=f"{DATA_ROOT}/train*.tfrecord",
        out_dir=COVS_ROOT
    )

    #   (reduce) Merge covariance matrices, using a 2-level reduce step: N->sqrt(N)->1 (implemented, need tree)
    root["Merge covariance matrices"] = co.Lazy(
        merge_covs_node,
        in_dir=COVS_ROOT,
        tmp_dir=MERGED_TMP,
        out_file=MERGED_FILE,
    )

    # Fit an OLS model using the covariance matrices (implemented, need tree)
    root["Models"] = co.Parallel()

    for ridge in [0, 1, 10, 100, 500]:
        name = "Linear" if ridge == 0 else f"Ridge={ridge}"
        model_node = co.Serial()

        model_node["Fit"] = co.Exec(
            commands.fit,
            in_path=MERGED_FILE,
            out_path=f"{MODEL_DIR}/{name}.pkl.gzip",
            ridge=ridge,
        )
        # Run a backtest on the validation data for each model (need to implement)
        model_node["Backtest"] = co.Lazy(
            backtest_node,
            model_path=f"{MODEL_DIR}/{name}.pkl.gzip",
            in_glob=f"{DATA_ROOT}/validate*.tfrecord",
            out_dir=f"{BACKTEST_ROOT}/{name}"
        )
        model_node["Merge backtests"] = co.Exec(
            commands.merge_backtest,
            in_paths=[f"{BACKTEST_ROOT}/{name}/validate*.pkl.gzip"],
            out_path=f"{BACKTEST_ROOT}/{name}/summary.pkl.gzip"
        )

        root["Models"][name] = model_node

    root["Summarize"] = co.Exec(
        commands.summarize,
        in_paths=[f"{BACKTEST_ROOT}/*/summary.pkl.gzip"]
    )
    return root


def download_node(data_root=DATA_ROOT, num_shards=500, max_shard=500) -> co.Parallel:
    output = co.Parallel()
    for ds in ["train", "validate", "test"]:
        output[ds] = co.Parallel()
        for shard in range(1, num_shards + 1):
            if shard > max_shard:
                break
            output[ds][f"shard_{shard}_of_{num_shards}"] = co.Exec(
                f"""
                set -x -o pipefail
                script=`pwd`/download.py
                mkdir -p {DATA_ROOT}
                cd {DATA_ROOT}
                shard={shard},{num_shards} partition=2/frame/{ds} mirror=us python $script
                """
            )
    return output


def compute_covs_node(in_glob, out_dir) -> co.Parallel:
    import glob
    import os
    in_files = sorted(glob.glob(in_glob))

    output = co.Parallel()
    for f in in_files:
        # Input: RAW_DATA_DIR/train3554.tfrecord
        # Output: COVS_ROOT/train3554.pkl.gzip
        base = os.path.basename(f).replace(".tfrecord", "")
        out_path = os.path.join(out_dir, base + ".pkl.gzip")

        if len(in_files) > 50:
            import re
            parent = re.sub("(\d\d)\d\d", "\\1__", base)
            if parent not in output:
                output[parent] = co.Parallel()
            base = f"{parent}/{base}"

        output[base] = co.Exec(commands.compute_cov, f, out_path)
    return output


def merge_covs_node(in_dir, tmp_dir, out_file) -> co.Serial:
    import glob
    import math
    import numpy as np
    in_files = sorted(glob.glob(f"{in_dir}/*.pkl.gzip"))

    tmp_files = []

    output = co.Serial()
    output["Stage1"] = co.Parallel()

    # Batch the files into sqrt(N)-sized chunks

    # In [1]: np.arange(0, 300, 14.5)
    # Out[1]:
    # array([  0. ,  14.5,  29. ,  43.5,  58. ,  72.5,  87. , 101.5, 116. ,
    #        130.5, 145. , 159.5, 174. , 188.5, 203. , 217.5, 232. , 246.5,
    #        261. , 275.5, 290. ])

    batch_size = math.sqrt(len(in_files))
    for i in np.arange(0, len(in_files), batch_size):
        start_idx = int(i)
        end_idx = int(i + batch_size)
        label = f"{start_idx}-{end_idx}"

        tmp_file = f"{tmp_dir}/{label}.pkl.gzip"
        output["Stage1"][label] = co.Exec(
            commands.merge_cov,
            in_paths=in_files[start_idx:end_idx],
            out_path=tmp_file
        )
        tmp_files.append(tmp_file)

    output["Stage2"] = co.Exec(
        commands.merge_cov,
        in_paths=tmp_files,
        out_path=out_file
    )

    return output


def backtest_node(model_path, in_glob, out_dir) -> co.Parallel:
    import glob
    import os

    in_files = sorted(glob.glob(in_glob))

    output = co.Parallel()
    for f in in_files:
        # Input: RAW_DATA_DIR/validate3554.tfrecord
        # Output: OUT_DIR/validate3554.pkl.gzip
        base = os.path.basename(f).replace(".tfrecord", "")
        out_path = os.path.join(out_dir, base + ".pkl.gzip")

        if len(in_files) > 50:
            import re
            parent = re.sub("(\d\d)\d\d", "\\1__", base)
            if parent not in output:
                output[parent] = co.Parallel()
            base = f"{parent}/{base}"

        output[base] = co.Exec(
            commands.backtest,
            model_path=model_path,
            data_path=f,
            out_path=out_path
        )
    return output


    return output


IMG = co.Image(copy_dir=".", install_pip=["conducto", "tensorflow", "matplotlib"])

if __name__ == "__main__":
    co.main(image=IMG)
