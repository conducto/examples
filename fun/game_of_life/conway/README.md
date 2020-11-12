# Conway's Game Of Life

This is a toy project, it includes several commands which together let the user play [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway's_Game_of_Life).  Its purpose is to provide building blocks for [a conducto demo](../README.md).

### The Commands

 - [to_grid](./life/stage.py)
 - [as_neighborhoods](./life/stage.py)
 - survive
 - reproduce
 - crowd
 - isolate
 - [to_png](./life/show.py)

# Installation

If you're debugging in a node container, you'll want to be able to see the effects of a code change without reinstalling, so consider using seuptools to install it in `develop` mode

    python setup.py develop

# Unit tests

    pytest -s live/*.py
