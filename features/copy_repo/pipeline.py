import conducto as co

IMG = co.Image(dockerfile="./Dockerfile", context=".", copy_repo=True, path_map={'.':'/usr/local/src/myapp'})

def main() -> co.Parallel:
    with co.Parallel(image=IMG) as root:
        root["count underscores"] = co.Exec(
            """
            set -euox pipefail
            myfiglet | tr -cd '_' | wc -c | tee count.txt
            grep '59' count.txt
            """)
        root["tree returns zero"] = co.Exec(
            """
            set -euox pipefail
            mytree
            """)
    return root

if __name__ == "__main__":
    co.main(default=main)
