import conducto as co
import glob
import gzip
import os
import pickle
import typing

N_Y_COLS = 3862


class Cov:
    def __init__(self, xx, xy, yy, n):
        self.xx = xx
        self.xy = xy
        self.yy = yy
        self.n = n

    def __iadd__(self, other):
        self.xx += other.xx
        self.xy += other.xy
        self.yy += other.yy
        self.n += other.n
        return self


class BacktestResult:
    def __init__(self, vid, predicted, actual):
        self.data = {vid: (predicted, actual)}

    def __iadd__(self, other):
        self.data.update(other.data)
        return self

    @staticmethod
    def from_data(data):
        output = BacktestResult(None, None, None)
        output.data = data
        return output


def compute_cov(in_path, out_path):
    """
    Analyze the data at `in_path`, compute the covariance matrices, and dump to `out_path`
    """
    import numpy as np
    cov = None

    xx = xy = yy = None
    for vid_id, labels, x_rows, y_row in _get_data(in_path):
        n_frames = len(x_rows)
        print(f"Video id={vid_id} has {n_frames} frames and labels={labels}")

        # Stack the arrays into matrices. This could be done faster by initially
        # allocating an array of the proper size and assigning into it, rather than
        # doing this second pass but ¯\_(ツ)_/¯.
        x = np.stack(x_rows, axis=0)
        y1 = np.stack([y_row], axis=0)
        yN = np.stack([y_row] * n_frames, axis=0)

        # Compute covariances. Reuse a preallocated buffer to store the result, rather
        # than allocating a new one each time. Also do y'y on a single row then multiply
        # by N, rather than doing redundant matrix multiplications on N copies of the
        # same row.
        xx = np.dot(x.T, x, out=xx)
        xy = np.dot(x.T, yN, out=xy)
        yy = np.dot(y1.T, y1, out=yy) * n_frames
        new_cov = Cov(xx, xy, yy, n_frames)

        if cov is None:
            # Make a copy of the matrices, and leave the originals to be reused to store
            # each incremental update.
            cov = Cov(np.array(xx), np.array(xy), np.array(yy), n_frames)
        else:
            cov += new_cov

    print(f"Saving to {out_path}")
    _write_obj(vars(cov), out_path)
    print("Done!")


def merge_cov(in_paths: typing.List[str], out_path):
    files = sorted(f for in_path in in_paths for f in glob.glob(in_path))
    cov = None
    for file in files:
        print("Reading in", file)
        new_cov = Cov(**_read_obj(file))
        if cov is None:
            cov = new_cov
        else:
            cov += new_cov
    print("Writing output to", out_path)
    _write_obj(vars(cov), out_path)
    

def fit(in_path, out_path, ridge=0):
    import matplotlib.pyplot as plt
    import numpy as np

    print("Reading", in_path)
    cov = Cov(**_read_obj(in_path))
    print()

    if ridge != 0:
        print("Applying adjustment for Ridge regression")
        xx_beta = cov.xx + np.identity(cov.xx.shape[0], cov.xx.dtype) * ridge * cov.n
        print()
    else:
        xx_beta = cov.xx

    print(f"Calculating β = `(X'X)^-1 * X' * Y`. X'X.shape={xx_beta.shape}, X'Y.shape={cov.xy.shape}")
    inv = np.linalg.pinv(xx_beta)
    beta = np.dot(inv, cov.xy)
    print(f"β.shape={beta.shape}")
    print()

    print("Calculating R^2 = (2 Yh'Y - Yh'Yh) = (2 * β' * X'Y - β' * X'X * β)")
    yhy = np.dot(beta.T, cov.xy)
    yhyh = np.dot(np.dot(beta.T, cov.xx), beta)
    r2 = np.diag((2 * yhy - yhyh) / cov.yy)
    print("In-sample R^2 =", r2)
    print()

    co.nb.matplotlib_inline()
    plt.plot(r2)
    plt.title("In-sample R^2 by label number")
    plt.show()

    print("Writing coefficients to", out_path)
    _write_obj(beta, out_path)


def backtest(model_path, data_path, out_path):
    import numpy as np

    beta = _read_obj(model_path)
    output = None
    for vid_id, labels, x_rows, y_row in _get_data(data_path):
        print("Analyzing video", vid_id)
        x = np.stack(x_rows, axis=0)
        yh_frame = np.dot(x, beta)
        yh_agg = np.mean(yh_frame, axis=0)

        top_5 = np.argsort(yh_agg)[-1:-6:-1]
        pred_labels = {i:yh_agg[i] for i in top_5}

        new_res = BacktestResult(vid_id, pred_labels, list(labels))
        if output is None:
            output = new_res
        else:
            output += new_res

    print("Writing outputs to", out_path)
    _write_obj(vars(output), out_path)


def merge_backtest(in_paths: typing.List[str], out_path):
    files = sorted(f for in_path in in_paths for f in glob.glob(in_path))
    obj = None
    for file in files:
        print("Reading in", file)
        new_obj = BacktestResult.from_data(**_read_obj(file))
        if obj is None:
            obj = new_obj
        else:
            obj += new_obj
    print("Writing output to", out_path)
    _write_obj(vars(obj), out_path)


def summarize(in_paths: typing.List[str]):
    files = sorted(f for in_path in in_paths for f in glob.glob(in_path))
    for file in files:
        result = BacktestResult.from_data(**_read_obj(file))
        true_positive = 0
        false_positive = 0
        false_negative = 0
        for predicted_dict, actual in result.data.values():
            predicted_set = set(predicted_dict.keys())
            actual_set = set(actual)
            true_positive += len(predicted_set & actual_set)
            false_positive += len(predicted_set - actual_set)
            false_negative += len(actual_set - predicted_set)
        print(f"{file:60}    Correct: {true_positive}   Wrong: {false_positive}    Missed: {false_negative}")


def _get_data(file):
    import numpy as np
    import tensorflow as tf
    tf = tf.compat.v1

    for i, example in enumerate(tf.python_io.tf_record_iterator(file)):
        tf_example = tf.train.Example.FromString(example)
        vid_id = (
            tf_example.features.feature["id"]
            .bytes_list.value[0]
            .decode(encoding="UTF-8")
        )

        tf_seq_example = tf.train.SequenceExample.FromString(example)
        n_frames = len(tf_seq_example.feature_lists.feature_list["audio"].feature)

        # Compute Y by 1-hot encoding the labels
        y_row = np.zeros(N_Y_COLS, dtype=int)
        labels = tf_example.features.feature["labels"].int64_list.value
        y_row[labels] = 1

        # Compute X by iterating through the frames and concatenating rgb and audio features
        x_rows = []
        for j in range(n_frames):
            rgb = tf.cast(
                tf.decode_raw(
                    tf_seq_example.feature_lists.feature_list["rgb"]
                    .feature[j]
                    .bytes_list.value[0],
                    tf.uint8,
                ),
                tf.float32,
            ).numpy()
            audio = tf.cast(
                tf.decode_raw(
                    tf_seq_example.feature_lists.feature_list["audio"]
                    .feature[j]
                    .bytes_list.value[0],
                    tf.uint8,
                ),
                tf.float32,
            ).numpy()
            x_row = np.concatenate([rgb, audio])

            x_rows.append(x_row)

        yield vid_id, labels, x_rows, y_row


def _write_obj(obj, file):
    text = pickle.dumps(obj)
    os.makedirs(os.path.dirname(os.path.abspath(file)), exist_ok=True)
    with gzip.open(file, "w", compresslevel=3) as f:
        f.write(text)


def _read_obj(file):
    with gzip.open(file, "r") as f:
        text = f.read()
    return pickle.loads(text)


if __name__ == "__main__":
    co.main()
