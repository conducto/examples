# Local Microservices

This example deploys, tests, and cleans up a simple app.
The app is made of two services: [Redis](https://redis.io) and [Flask](https://flask.palletsprojects.com).
- Flask responds to http requests and increments a counter.
- Redis stores the counter.

The pipeline deploys them as docker containers, and tests them.
There is a clean-up step which stops the containers at the end.

### To Run

    python ./pipeline.py --local
