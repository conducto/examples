import conducto as co
import tour

def pipeline() -> co.Serial:
    """
    Include code from a git repo
    """

    root["todo"] = co.Exec(f":")


    root = tour.guide(root)     # nothing to see here

    return root


if __name__ == "__main__":
    co.main(default=pipeline)
