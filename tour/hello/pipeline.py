# hello.py
import conducto as co

py_code = 'print("Hello")'
js_code = 'console.log("World!")'

def pipeline() -> co.Serial:
    """
    Welcome to Conducto
    """
    root = co.Serial()
    root["hello from python"] = co.Exec(f"python -c '{py_code}'")
    root["world from javascript"] = co.Exec(
        f"echo '{js_code}' | node -"
        # image="alpine-current:latest" # <-- uncomment to fix
    )
    return root


if __name__ == "__main__":
    co.main(default=pipeline)
