import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dagshub",
    version="0.1.99-alpha",
    author="DagsHub",
    author_email="contact@dagshub.com",
    description="DagsHub client libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DagsHub/client",
    packages=setuptools.find_packages(),
    install_requires=["PyYAML>=5", "requests>=2", "fusepy>=3"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "dagshub-mount = dagshub.streaming.mount:main",
        ]
    }
)
