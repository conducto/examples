import time
import os

import redis
from flask import Flask

tag = os.environ["TAG"]
redis_host = os.environ["REDIS_HOST"]
redis_port = os.environ["REDIS_PORT"]
redis_password = os.environ["REDIS_PASSWORD"]

app = Flask(__name__)
cache = redis.Redis(host=redis_host, port=redis_port, password=redis_password)


def get_hit_count():
    retries = 5
    while True:
        try:
            # add one
            val = cache.incr(tag)

            # add two
            # val = cache.incr(cache.incr(redis_key))
            return val
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


@app.route("/")
def how_many():
    count = get_hit_count()
    return "Served {} requests\n".format(count)
