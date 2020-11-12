import collections
from flask import Flask, request
import json

app = Flask(__name__)
DATA = collections.defaultdict(dict)


@app.route("/")
def hello_world():
    return "Hello, Conducto!"


@app.route("/user/<username>", methods=["GET", "POST"])
def user_profile(username):
    if username == "hacker":
        return json.dumps({"error": "Unauthorized"}), 401

    if request.method == "POST":
        # For POST messages, set the key & value for the
        # user profile.
        data = request.get_json()
        key = data["key"]
        value = data["value"]

        # Set them in DATA under this username
        DATA[username][key] = value

    # Return the data stored so far for this user
    output = json.dumps({"user": username, "data": DATA[username]})
    return output, 200
