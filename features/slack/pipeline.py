import conducto as co
from sensors import get_data
from aws import host_file
from pathlib import Path

# the contents of /conducto/data/pipeline persist between nodes
plot_path = "/conducto/data/pipeline/plots/coherence.png"
report_path = "/conducto/data/pipeline/metadata/coherence.txt"


def get_sensor_data():
    "Anyone out there?"

    # make dirs
    for file in [plot_path, report_path]:
        Path(file).parent.mkdir(exist_ok=True)

    # get sensor data
    coherence = get_data(write_file=plot_path)

    # save a metric separately
    with open(report_path, "w") as f:
        f.write(str(coherence))


def looks_like_aliens():

    with open(report_path, "r") as f:
        coherence = float(str(f.read()))

    return coherence > 0.85


# plot message bits
title = "we get signal"
alt_text = "plots of two signals and their degree of coherence"
markdown_disclaimer = f"""
### {title}
**Don't share this** until it is confirmed by the other facilities.
"""


def plot_to_stdout():
    "Display results to pipeline viewer"

    # /conducto/data/pipeline is assumed
    url = co.data.pipeline.url("plots/coherence.png")
    print(
        f"""
<ConductoMarkdown>
{markdown_disclaimer}
![{alt_text}]({url})
</ConductoMarkdown>
        """.strip()
    )


# use '#channelname' or 'username'
update_channel = "#interesting-signals"
update_users = ["EArroway", "SRHadden"]

slack = co.integrations.slack.Slack()

slack_disclaimer = f"""
*{title}*
_Don't share this_ until it is confirmed by the other facilities.
"""

bucket_name = "conducto-test-bucket"


def plot_to_slack():
    "Send a slack message using the blocks api"
    # see https://api.slack.com/reference/block-kit/blocks

    # this requires some place to host the image
    url = host_file(plot_path, bucket_name)

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": slack_disclaimer},
        },
        {"type": "divider"},
        {
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": title,
            },
            "block_id": "image4",
            "image_url": url,
            "alt_text": alt_text,
        },
    ]

    if looks_like_aliens():
        blocks.insert(
            3,
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "does that look like :alien: to you?",
                },
            },
        )

    # send the message
    slack.message("#interesting-signals", blocks=blocks)


def message_to_slack_user(recipient):
    "Send a text-only slack message"

    if looks_like_aliens():
        slack.message(
            recipient,
            text="Check out #interesting-signals, you're going to want to see this.",
        )
        print(f"notified {recipient}")
    else:
        print("boring data, not notifying")


img = co.Image(
    copy_dir=".",
    install_pip=["conducto", "numpy", "matplotlib", "boto3"],
)


def main() -> co.Serial:

    with co.Serial(image=img) as p:  # p is for 'Pipeline root'

        p["get data"] = co.Exec(get_sensor_data)
        p["notify"] = co.Parallel()
        p["notify/stdout"] = co.Exec(plot_to_stdout)
        p["notify/channel"] = co.Exec(plot_to_slack)
        p["notify/team"] = co.Serial()
        for user in update_users:
            p[f"notify/team/{user}"] = co.Exec(message_to_slack_user, user)

    return p


if __name__ == "__main__":
    co.main(default=main)
