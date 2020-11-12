import conducto as co

cmd = "cat /etc/*-release | egrep '^NAME'"


def which_distro() -> co.Serial:
    pipeline = co.Serial()
    pipeline["Node Name"] = co.Exec(cmd)
    return pipeline


if __name__ == "__main__":
    co.main(default=which_distro)
