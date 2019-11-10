import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dagshub",
    version="0.0.1",
    author="Guy Smoilovsky",
    author_email="guy@dagshub.com",
    description="DAGsHub client libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dagshub/dagshub-client",
    packages=setuptools.find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
