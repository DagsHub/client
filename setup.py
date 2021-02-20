import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dagshub",
    version="0.1.6",
    author="DAGsHub",
    author_email="contact@dagshub.com",
    description="DAGsHub client libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DAGsHub/client",
    packages=setuptools.find_packages(),
    install_requires=["PyYAML>=5"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
