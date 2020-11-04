# Hello World

This example includes two commands.
One of them has a problem.
Your challenge is to fix it.

## Pipeline Definition

The left pane lets you view the files in this project.
You're looking at `README.md` right now.
If you select `pipeline.py` you'll see a pipeline definition instead.

There you'll find a function called `pipeline()`.
It returns an object that Conducto uses to build the tree in the pane to the right.
There you'll find clues about the problem.

## Pipeline Instance

Nodes will turn red or green when they are finished running.
You can click each node to see more information about it.

### Root Node: `/`

Conducto pipelines are trees, and root is called `/`.
Select it.

#### Reset It

If it's not running, try resetting it.
The child nodes will rerun automatically if "run" is enabled.

#### P Q R D E K

The row of numbers in the **Results** section of the root node shows how many children are...

- **P** ending
- **Q** ueued
- **R** eset
- **D** one
- **E** rrored
- **K** illed


#### Explore the Pipeline Tree

To examine the first `Exec` node, press the down arrow key or click it in the tree.

### Child Node: `/hello`

You can alter pipeline commands without changing the code.
Use the pencil icon to change the command.

```
    # python -c 'print("Hello")'
    python -c 'print("Hey There")'
```

Then reset the node.
Once it finishes, select entries in **Timeline** to view each execution.

### Child Node: `/world`

This Node Fails.
To understand why:

- Take a look at **Stderr**.
- Then click "conducto-default" in the **Image** parameter box.

#### Missing Software

This node's image is based on [`python:3.8-slim`](https://hub.docker.com/_/python) .
The command fails because node.js is not in this image.

Image assignment can only be done in the definition.
To fix it:

 - assign [`node:current-alpine`](https://hub.docker.com/_/node") as this `/world`'s image.
 - save `pipeline.py`
 - reset the failing node

# Summary

The failing node referenced software that was missing from its image.

The fix was to edit the pipeline definition so it used an image with Node.js.

If all of this pipeline's nodes are green, you've completed this example.

#### Related Docs:

- [Pipeline Structure](/docs/basics/pipeline-structure)
- [Controlling a Pipeline](/docs/basics/controlling-a-pipeline)
