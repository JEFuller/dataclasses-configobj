import os.path
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

setup(
    name="dataclasses-configobj",
    version="0.0.3",
    description="Easily deserialize Data Classes from ini files",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/JEFuller/dataclasses-configobj",
    author="Dave Tapley",
    author_email="dave@jefuller.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    packages=["dataclasses_configobj"],
    include_package_data=True,
    install_requires=["configobj", "typing-inspect"],
)