#!/usr/bin/env python3
import setuptools
from setuptools.command.install import install

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("./src/_about.py", "r") as fa:
    about = {}
    exec(fa.read(), about)

class DownloadNLTK(install):
    def run(self):
        self.do_egg_install()
        import nltk
        nltk.download('wordnet')
        nltk.download('omw-1.4')

setuptools.setup(
    name=about["__name__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__author_email__"],
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
    python_requires=">=3.7, <3.8",
    install_requires=[
        "beautifulsoup4==4.8.2",
        "en_core_web_sm@https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.5/en_core_web_sm-2.2.5.tar.gz",
        "googletrans",
        "idna==2.8",
        "langdetect==1.0.7",
        "nltk==3.7",
        "numpy==1.21.6",
        "owlready2",
        "python-Levenshtein",
        "pyyaml",
        "rdflib==5.0.0",
        "regex",
        "requests==2.28.1",
        "spacy==2.2.3",
        "spacy-langdetect==0.1.2",
        "spelchek",
        "torch@https://download.pytorch.org/whl/cpu/torch-1.7.0%2Bcpu-cp37-cp37m-linux_x86_64.whl",
        "torchvision@https://download.pytorch.org/whl/cpu/torchvision-0.8.1%2Bcpu-cp37-cp37m-linux_x86_64.whl",
        "torchaudio@https://download.pytorch.org/whl/torchaudio-0.7.0-cp37-cp37m-linux_x86_64.whl",
        "transformers==4.22.0",
        "translate",
    ],
    cmdclass={'download_nltk': DownloadNLTK}
)

