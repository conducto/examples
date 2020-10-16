# counter

This example deploys, tests, and cleans up a simple app.
The app is made of two services: [Redis](https://redis.io) and [Flask](https://flask.palletsprojects.com).
- Flask responds to http requests and increments a counter.
- Redis stores the counter.

The pipeline deploys them as docker containers, and tests them.
There is a clean-up step too, but it starts skipped so that you can play around manually before tearing it down.

### To Run

    python ./pipeline.py --local

### While it's up

- Take your browser to [http://localhost:5000](http://localhost:500) and hit refesh a few times.
- Run `docker ps` to see the services that we deployed.
- Run `docker logs <contaier-id>` to see what's up with the deployed services.

### Tear it down

- When you're done, unskip the last node and let it clean up.
- Run `docker ps` again to see that the services are gone.
