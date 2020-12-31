"Define a CI/CD pipeline."

import conducto as co


def pr(branch) -> co.Parallel:
    # Boilerplate: Define Docker image with code from repo.
    image = co.Image(copy_repo=True, copy_branch=branch)

    # Run commands in parallel to interact with repo's files.
    #
    # co.Parallel: run children at same time
    # co.Serial: run children one after another
    # co.Exec: run a shell command in a container
    #
    # TODO: Add your own commands to build, test, and deploy.
    with co.Parallel(image=image) as root:
        co.Exec(f"echo {branch}", name="print branch")
        co.Exec("pwd", name="print working directory")
        co.Exec("ls -la", name="list files")

    # Boilerplate: Add GitHub status callbacks.
    co.git.apply_status_all(root)

    return root


def deploy() -> co.Serial:
    raise NotImplementedError("TODO: Implement deploy pipeline.")


# Boilerplate: Expose commands from .conducto.cfg.
if __name__ == "__main__":
    co.main()
