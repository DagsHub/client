import setuptools

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dagshub",
    version="0.2.0",
    author="DagsHub",
    author_email="contact@dagshub.com",
    description="DagsHub client libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DagsHub/client",
    packages=setuptools.find_packages(),
    install_requires=[
        "PyYAML>=5",
        "requests>=2",
        "fusepy>=3",
        "appdirs>=1.4.4",
        "pytimedinput>=2.0.1",
        "click>=8.0.4"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "dagshub = dagshub.common.cli:cli"
        ]
    }
)
