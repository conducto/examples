# image_version

Runs a command in a docker image whose version is pinned to a specific hash.  Specifically `alpine@sha256:185518070891758909c9f839cf4ca393ee977ac378609f700f60a771a2dfe321`.  This way the command will always use the same image.

This isolates the pipeline against changes made by the maintainers of the `alpine` image on DockerHub.

### To get an image hash

    $ docker pull alpine:latest

        latest: Pulling from library/alpine
        Digest: sha256:185518070891758909c9f839cf4ca393ee977ac378609f700f60a771a2dfe321
        Status: Downloaded newer image for alpine:latest
        docker.io/library/alpine:latest

    $ docker inspect alpine:latest --format '{{json .RepoDigests}}'

        ["alpine@sha256:185518070891758909c9f839cf4ca393ee977ac378609f700f60a771a2dfe321"]

### To Run

    python ./pipeline.py --local

### Related

#### Concepts

- [Potentially Malicious Pipelines](https://www.conducto.com/docs/basics/agents#potentially-malicious-pipelines)

#### API's

- [Image](https://conducto.com/api/docker.html#conducto.Image)
