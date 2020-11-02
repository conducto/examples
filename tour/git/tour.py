# A normal pipeline definition wouldn't need to hide things from its reader.
# But since this is a tour, we want to keep the definition minimal and show
# hepful text on the pipeline instance and not in the definition too.

from inspect import cleandoc
import conducto as co

def guide(root):
    """
    Attach helpful messages
    """


    return root

def stop_summary():
    summary = co.Exec(":", doc=cleandoc(
        """
        #### Summary

        A node failed because it referenced software from the wrong git repo.

        This problem is easy to discover from a debug shell.

        A few ways to fix it:
        - Set it explicitly by setting the `repo_url` image parameter.
        - Let Conducto guess by setting `copy_repo=True`.

        If all of this pipeline's nodes are green, you've completed this example.

        #### Related Docs:

        - [Tour Map](/docs/getting-started/tour)
        - [Images](/docs/basics/images)
        - [Debugging](/docs/basics/debugging)
        - [Hello Git (example)](https://github.com/conducto/examples/blob/main/hello_git/pipeline.py)

        #### A fork in the road:

        - [Explore how Conducto manipulates Docker containers.](app/sandbox/github/conducto/examples?dir=tour/reuse&preview_file=pipeline.py)
        - [Call Docker directly from a pipeline node.](app/sandbox/github/conducto/examples?dir=tour/docker&preview_file=pipeline.py)

        """))

    return summary
