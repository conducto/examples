# hello.py
import conducto as co

py_code = 'print("Hello")'
js_code = 'console.log("World!")'


def pipeline() -> co.Serial:
    root = co.Serial()
    root["hello from python"] = co.Exec(f"python -c '{py_code}'")
    root["world from javascript"] = co.Exec(
        f"echo '{js_code}' | node -", image="node:current-alpine"
    )
    return root


if __name__ == "__main__":
    co.main(default=pipeline)
