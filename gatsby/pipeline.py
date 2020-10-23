import conducto as co


def cicd() -> co.Serial:
    image = co.Image(
        "node:current-alpine",
        copy_url="https://github.com/gatsbyjs/gatsby-starter-blog",
        copy_branch="master",
        reqs_packages=["autoconf"],
        reqs_py=["conducto"],
    )
    root = co.Serial(image=image, container_reuse_context=co.ContainerReuseContext.NEW)
    root["install"] = co.Exec("npm i --silent")
    root["test"] = co.Exec("CI=true npm test", skip=True)
    root["build"] = co.Exec("CI=true npm run build")
    root["tar"] = co.Exec("tar -cvzf latest-build.tgz public")
    root["save"] = co.Exec("conducto-data-user put latest-build.tgz latest-build.tgz")
    return root


if __name__ == "__main__":
    co.main(default=cicd)
