import sys
import conducto as co

img = co.Image(copy_dir=".", reqs_py=["conducto"])


# achieves a node state of done (0) or error (1)
def certain(code):
    sys.exit(int(code))


def poll_sensors() -> co.Serial:

    r = co.Serial()
    r['/pmt'] = co.Serial()
    r['/pmt/poll'] = co.Parallel(image=img)
    for name in range(1104):

        if name == 1002:
            # presumably this sensor is broken somehow
            r[f'/pmt/poll/{name}'] = co.Exec(certain, 1)
        else:

            # most of the sensors work just fine
            r[f'/pmt/poll/{name}'] = co.Exec(certain, 0)

    run_callback = co.callback.slack_status(
        recipient="SlackUser",
        message="polling sensors"
    )
    r.on_running(run_callback)

    err_callback = co.callback.slack_status(
        recipient="#array-status",
    )
    r.on_error(err_callback)

    done_callback = co.callback.slack_status(
        recipient="#array-status",
        message="all sensors reporting nominally",
    )
    r.on_done(done_callback)

    # other events include:
    # - on_queued
    # - on_running
    # - on_killed
    # - on_state_change

    return r


if __name__ == "__main__":
    co.main(default=poll_sensors)
