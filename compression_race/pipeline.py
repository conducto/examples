import conducto as co

# five randomly generated payloads
# ranging in size from 50m to 250m
payloads = co.Image(dockerfile='Dockerfile', context='.')

def go() -> co.Parallel:
    with co.Serial(image=payloads, cpu=2) as root:

        # use five containers to compress five files
        with co.Parallel(name='container parallelism'):
            for i in range(5):
                co.Exec(f'gzip -1 payload{i + 1}.dat',
                        name=f"worker {str(i)}")

        # use five threads to compress five files
        root['process parallelism'] = \
            co.Exec('ls payload*.dat | parallel gzip -1')

        # compress five files in a row
        co.Exec('gzip -1 payload*.dat', name="no parallelism")

    return root

if __name__ == "__main__":
    co.Image.register_directory("CONDUCTO_DEMO", ".")
    co.main(default=go)
