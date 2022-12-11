import setuptools
import os.path


# Thank you pip contributors
def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="dagshub",
    version=get_version("dagshub/__init__.py"),
    author="DagsHub",
    author_email="contact@dagshub.com",
    description="DagsHub client libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DagsHub/client",
    packages=setuptools.find_packages(),
    install_requires=[
        "PyYAML>=5",
        "fusepy>=3",
        "appdirs>=1.4.4",
        "pytimedinput>=2.0.1",
        "click>=8.0.4",
        "httpx>=0.22.0",
        "GitPython>=3.1.29",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "dagshub = dagshub.common.cli:cli"
        ]
    }
)
