with co.Parallel() as root:
    with co.Serial(name="run until error"):

        # will fail because grep returns nonzero
        co.Exec('echo foo | grep bar', name="fail")

        # will remain pending because the previous node failed
        co.Exec('echo baz', name="succeed")

    with co.Serial(stop_on_error=False, name="run all children"):

        # will fail because grep returns nonzero
        co.Exec('echo wakka | grep bang', name="fail")

        # will run and succeed despite the earlier failure
        co.Exec('echo splat', name="succeed")
