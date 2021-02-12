import boto3
import os
from datetime import datetime
from pathlib import Path

def host_file(abs_path, bucket_name):
    """
    Host the file in S3.

    This assumes that the bucket exists and you have write access to it.
    The bucket will also need a policy that makes new objects readable.
    """
    # https://stackoverflow.com/a/23102551/1054322

    # you'll need to add these to your conducto profile
    key_id = os.environ["AWS_ACCESS_KEY_ID"]
    secret = os.environ["AWS_SECRET_ACCESS_KEY"]

    client = boto3.client("s3", aws_access_key_id=key_id, aws_secret_access_key=secret)

    stamp = datetime.now().strftime("%s")
    print(f"uploading {abs_path}")
    path = Path(abs_path)
    obj_name = '.'.join([path.stem, stamp, path.suffix[1:]])

    response = client.upload_file(abs_path, bucket_name, obj_name)

    url = f"https://{bucket_name}.s3.amazonaws.com/{obj_name}"
    print(f"url: {url}")
    return url
