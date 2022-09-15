#!/usr/bin/env python3
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("./src/_about.py", "r") as fa:
    about = {}
    exec(fa.read(), about)

setuptools.setup(
    name=about["__name__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email="felix.ocker@googlemail.com",
    description="production ontology merging framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about["__url__"],
    project_urls={
        "Bug Tracker": "https://github.com/felixocker/prom/issues",
    },
    download_url=about["__download_url__"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    keywords=about["__keywords__"],

    include_package_data=True,  # include non-code files during installation
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires="=3.7",
    install_requires=[
    ],
)

