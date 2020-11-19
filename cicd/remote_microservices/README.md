# Remote Microservices

This example tests and deploys a simple app.
If you've seen the *Local Microservices* example, the app will be familliar.

The app is made of two services: [Redis](https://redis.io) and [Flask](https://flask.palletsprojects.com).
- Flask responds to http requests and increments a counter.
- Redis stores the counter.

The pipeline deploys to a "test" app remotely, and then tests it.

### You Will Need

- A [Heroku account](https://signup.heroku.com/)
- A [RedisLabs account](https://redislabs.com/#signup-modal)

We'll be sticking to the free tiers of both.

### Store Access Details

- If you have a Conducto account, add your account details to your user's secrets.
- If you don't have a Conducto account, hard-code them into `access.py`.

See [access.py](access.py) for instructions.


### Things to Try

You can launch this pipeline a few different ways.

- Clone this repo and run a command for one of the modes below
- If you're in a sandbox, see the bottom of [pipeline.py](pipeline.py) to change modes.
- Put this directory in a repo of its own and have the [Conducto github integration]() call it.

The deploy nodes for both test and prod write urls to stdout.
Paste them into a browser to manually test the deployment.

Try refreshing a few times.

Theres a commented out code change in [app.py](app.py).
Enable it, deploy, and see that your code was deployed.

#### Dev-Env Mode (local)

    python pipeline.py test --local --run

- Gets code from the local filesystem
- Tests it on external test infra
- Stops after reporting results

#### CI Mode (PR)

    python pipeline.py pr my_branch --cloud --run

- Gets code from the "my_branch"
- Tests it on external test infra
- Stops after reporting results

#### CI+CD Mode (merge)

    python pipeline.py merge --cloud --run

- Gets code from the "main" branch (hardcoded)
- Tests it on external test infra
- If tests pass, deploys it to external prod infra

### Teardown

The teardown steps are included in every pipeline, but they're skipped.
To tear down a deployment, unskip its node.
