# hello_py

A repo-sourced hello world.  Compares explicit references to an external repo with implicit references to its own repo.

### External Repo, No Local Code

Use `copy_url` to clone code from an external repo:

    python ./pipeline.py --local

### External Repo, Local Code for Debug Sessions

Like above, but use `path_map` to mount local code in `./local-copy` for use in debug sessions:

    python ./pathmap.py --local

Note how contents of [./local-copy](./local_copy) resemble the contents of https://github.com/leachim6/hello-world.
In live debug sessions, they'll be mounted instead of the files from the repo so that you can try uncommitted changes in the container.

### This Repo, Local Changes Ignored


Use `copy_repo` to detect the parent repo (this one) and clone it:

    python ./pathmap.py --local copy


### Related

#### Concepts

- [Image Handling](https://www.conducto.com/docs/basics/images#adding-files-via-git)

#### API's

- [Image](https://conducto.com/api/docker.html#conducto.Image)
- [Node](https://conducto.com/api/nodes.html)
