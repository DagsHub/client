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

install_requires = [
    "PyYAML>=5",
    "appdirs>=1.4.4",
    "click>=8.0.4",
    "httpx>=0.23.0",
    "GitPython>=3.1.29",
    "rich>=13.1.0",
    # Need to keep dacite version in lockstep with voxel, otherwise stuff breaks on their end
    "dacite~=1.6.0",
    "tenacity>=8.2.2",
    "gql[requests]",
    "dataclasses-json",
    "pandas",
    "treelib>=1.6.4",
    "pathvalidate>=3.0.0",
    "python-dateutil",
    "boto3",
    "dagshub-annotation-converter>=0.1.0",
]

extras_require = {
    "jupyter": ["rich[jupyter]>=13.1.0"],
    "fuse": ["fusepy>=3"],
    "autolabeling": ["ngrok>=1.3.0", "cloudpickle>=3.0.0"],
}

packages = setuptools.find_packages(exclude=["tests", "tests.*"])

setuptools.setup(
    name="dagshub",
    version=get_version("dagshub/__init__.py"),
    author="DagsHub",
    author_email="contact@dagshub.com",
    description="DagsHub client libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DagsHub/client",
    packages=packages,
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["dagshub = dagshub.common.cli:cli"]},
)
