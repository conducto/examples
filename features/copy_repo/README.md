# copy_repo

This example shows how your pipeline can use local code while you debug, and remote code when triggered by an [integration](https://conducto.com/docs/integrations).

[Dockerfile](./Dockerfile) says:
```
COPY . /usr/local/src/myapp
```

The challenge is to make '/usr/local/src/myapp' contain the right code at the right times.  We achieve it like this:

[pipeline.py](./pipeline.py) says:

```
IMG = co.Image(dockerfile="./Dockerfile",
               context=".",
               copy_repo=True,
               path_map={'.':'/usr/local/src/myapp'})
```

- `dockerfile` path to the Dockerfile for this image
- `context` path to the Docker build context for this image
- `copy_repo` let Conducto choose the git source
- `path_map` when debugging, mount local file at this location

(All relative paths are relative to the location of the pipeline definition)

# Scenarios

There are a few ways to run this app

 - Without Docker or Conducto
 - Without Conducto
 - User-Launched Conducto Pipeleine
 - Integration-Launched Conducto Pipeline
 - Debuging with Live code

Each gets a amall section below.

## Without Docker or Conducto

`python setup.py develop` or `pip install -e .` are two ways to ensure that the installation process doesn't make any copies of your code.
This is helpful during development because you can edit the code and rerun it without needing to run `python setup.py install` or `pip install .` over and over again.

## Docker Only, No Conducto

This command will create a docker image:

```
docker build . -t myappimg
```

The installation commands in [`Dockerfile`](./Dockerfile) handle app setup, and you can run it with something like:

```
docker run myappimg
```

## User Launched, No Live Code

If you're launching a pipeline manually, `copy_repo=True` tells Conducto to use files local to wherever you're launching it from.
This happens when you launch a pipeline like `python pipeline.py --local` or `python pipeline.py --cloud`

The diagram on the ["Images" docs page](https://www.conducto.com/docs/basics/images) shows how this works.
**first** the Docker build runs.
In this example, it copies some local files into the image.
**then** Conducto copies the code into the image (potentially a second time).

This might seem a bit silly, but keep in mind that you can also depend on docker images that you don't build yourself.  In these cases, it could be useful to pull the image from a repository and then have Conducto copy updated code into it.

## Integration Launched, No Live Code

If a [Conducto Integtaion](https://www.conducto.com/docs/integrations) launches the pipeline, it clones a branch which [depends on the event](https://www.conducto.com/docs/integrations/github#events-and-parameters) that is launching this pipeline.
From there, the process continues like in the previous section.

## User Launched, Live Code

This is where `path_map` comes in.
If you opt to [debug live code](https://www.conducto.com/docs/basics/debugging#debugging-live-code) your local code will be mounted in the debug container.

In this example, the directory containing the pipeline definition gets mounted at `/usr/local/src/myapp` and hides whatever was copied into the image.
Since we used `pip install -e .`, the rest of the container filesystem is set up to reference code in that location, which lets you make changes in a local editor and have them show up in the debug session.
