import conducto as co

# Build a Docker image using contents of a Git repo
IMG = co.Image("python:3.8-slim",
    copy_url="https://github.com/conducto/examples", copy_branch="main",
    install_packages=["cloc"], install_pip=["pandas"]
)

def main() -> co.Parallel:
    with co.Parallel(image=IMG) as root:
        # Count lines of code in the remote Git repo.
        root["lines of code"] = co.Exec("cloc .")
        # Run a simple data analysis script located there.
        root["biggest US cities"] = co.Exec(
            "cd features/copy_url && python analyze.py cities.csv"
        )
    return root

if __name__ == "__main__":
    co.main(default=main)