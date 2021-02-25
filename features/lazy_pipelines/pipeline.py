import conducto as co


############################################################
# Main pipeline
############################################################
def main() -> co.Parallel:
    """
    Dynamically build pipelines for each actor in a static list.
    """
    actors = ["Oprah Winfrey", "Kate Mara", "Don Cheadle", "Dwayne Johnson"]
    root = co.Parallel(image=_get_image())
    for actor in actors:
        root[actor] = co.Lazy(
            f"python pipeline.py all_by_actor '{actor}'"
        )
    return root


############################################################
# Command line
############################################################
def all_by_actor(actor) -> co.Parallel:
    """
    Return a pipeline listing all Netflix shows with an actor.
    Call with co.Lazy to generate pipeline at runtime.
    """
    df = _load_data()
    titles = df[df.cast.str.contains(actor) | False].title

    output = co.Parallel()
    for title in titles:
        output[title] = co.Exec(
            f"python pipeline.py for_title {repr(title)}"
        )
    return output


def for_title(title):
    """
    Print Netflix record for one title
    """
    df = _load_data()
    return df[df.title == title].iloc[0].to_dict()


############################################################
# Helper functions
############################################################
def _load_data():
    import boto3
    import io
    import pandas as pd
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket="conducto-examples", Key="netflix_titles.csv")
    contents = response["Body"].read()
    return pd.read_csv(io.BytesIO(contents))


def _get_image():
    return co.Image(
        "python:3.8-slim",
        copy_dir=".",
        install_pip=["conducto", "boto3", "pandas"]
    )


if __name__ == "__main__":
    co.main(default=main)
