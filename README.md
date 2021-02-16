# Example Pipelines

This repo contains a variety of Conducto pipelines. Browse these examples, or check out the [docs](https://conducto.com/docs).

## CI/CD & DevOps
Continuous Integration and Continuous Deployment (CI/CD) is the automatic building, testing, and deployment of new code. 

Here are examples of Conducto pipelines that build, test, and deploy.

- [Flask app - local](./cicd/flask_microservice/): Lint, build, and test a Flask app, then deploy it locally with Docker.
- [Flask app - AWS](./cicd/aws_microservice/): Same Flask app as above, but deployed to AWS. Must supply your own AWS credentials.  
- [Local microservices](./cicd/local_microservices/): Deploy and clean up two microservices that talk to each other.

## Data Pipelines & Data Science
Data pipelines are easy! Just download data, merge it, compute features, run machine learning algorithms, backtest each one, and analyze backtests to pick the best model. You should run in parallel because the data can be big. Don't forget to illustrate your results with graphs. Of course the whole process should be easy to understand.

Data pipelines like that are straightforward in Conducto.

- [Predict churn](./data_science/predict_churn/): Combine sample user data with transaction data and build a model to predict customer churn.
- [Weather data](./data_science/weather_data/): Download US weather data and then visualize it.

## Features
These are pipelines that illustrate different features of Conducto.
- Several flavors of Hello World
  - [Python from shell](./features/hello_py/): Say "Hello" from Python.
  - [Python & JavaScript in shell](./features/hello_world): Nodes can have different environments. Say "Hello" in Python and "World" in JavaScript.
  - [Python & JavaScript in scripts](./features/hello_py_js/): Same as above, but execute scripts instead of specifying code on the command line.
  - [Git](./features/hello_git/): Load code from Git repos.
  - [Python functions](./features/hello_native/): Directly call Python functions in `Exec` nodes.
  - [Docker](./features/hello_docker/): Run Docker's builtin Hello World image.
  - [Dockerfile](./features/hello_dockerfile/): Use a custom Dockerfile to say hello with a Pokemon!
- [Container reuse](./features/container_reuse/): Conducto can go faster by reusing containers. Learn how to control this.
- [Passing arguments](./features/disambiguate): Nuances of argument passing with direct Python functions.
- [Lazy pipelines](./features/lazy_pipelines): Dynamically build pipelines at runtime, based on data.
- [Pinning image version](./features/image_version/): Specify a particular Docker image version for added security and reliability. 
- [Stop on error](./features/stop_on_error/): `Serial(stop_on_error=True/False)` gives you additional control for handling errors.
- [Tree syntax](./features/tree_syntax/): Shows the three different ways to assemble your tree, with different levels of readability vs reusability. 
- [Slack](./features/slack/): Send messages from Conducto pipelines to users and channels in Slack workspaces.

## Fun
Ever wanted to abuse your workflow manager to play Conway's Game of Life? So did we. Here are some weird things you can do with Conducto.
- [Game of Life](./fun/game_of_life/): Play Conway's Game of Life using Conducto. Make and display an animated GIF of the result.
- [Sieve of Eratosthenes](./fun/eratosthenes): Use the Sieve of Erastothenes to calculate all primes up to _n_.
- [Compression race](./fun/compression_race/): Perform the same workload multiple times, tweaking CPU resources to change how fast each one finishes.
- [Your daily fortune](./fun/fortune_messy/): Ask a fortune teller for your message for each day of the month.

## Tour
- A [guided tour](./tour) of Conducto for beginners.
