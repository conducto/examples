from setuptools import setup, find_packages

setup(
    name="myapp",
    version="0.1.0.dev1",
    description="unhelpful wrappers for popular utilities",
    packages=["myapp"],
    python_requires=">=3.6",
    install_requires=["sh"],
    entry_points={
        "console_scripts": [
            "mytree = myapp.mytree:main",
            "myfiglet = myapp.myfiglet:main",
        ]
    },
)
