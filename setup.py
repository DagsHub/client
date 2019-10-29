import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytorch-lightning-dagshub",  # Replace with your own username
    version="0.0.1",
    author="Guy Smoilovsky",
    author_email="guy@dagshub.com",
    description="Integration of pytorch-lightning with DAGsHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dagshub/pytorch-lightning-dagshub",
    packages=setuptools.find_packages(),
    install_requires=["pytorch-lightning>=0.5"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
