# AEA Framework

[![PyPI](https://img.shields.io/pypi/v/aea)](https://pypi.org/project/aea/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/aea)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/aea)
[![](https://img.shields.io/pypi/l/aea)](https://github.com/fetchai/agents-aea/blob/master/LICENSE)
![PyPI - Downloads](https://img.shields.io/pypi/dm/aea)
[![](https://img.shields.io/badge/slack-fetchai-black.svg)](https://fetch-ai.slack.com/join/shared_invite/enQtNDI2MDYwMjE3OTQwLWY0ZjAyYjM0NGQzNWRhNDMxMzdjYmVhYTE3NDNhNTAyMTE0YWRkY2VmOWRmMGQ3ODM1N2NjOWUwNDExM2U3YjY)

![AEA framework sanity checks and tests](https://github.com/fetchai/agents-aea/workflows/AEA%20framework%20sanity%20checks%20and%20tests/badge.svg?branch=master)
![Codecov](https://img.shields.io/codecov/c/github/fetchai/agents-aea)

A framework for autonomous economic agent (AEA) development

<p align="center">
  <img src="/data/aea.png?raw=true" alt="AEA Description" width="70%"/>
</p>

## Get started

1. Create and launch a clean virtual environment with Python 3.7 (any Python `>=` 3.6 works):

       pipenv --python 3.7 && pipenv shell

2. Install the package from [PyPI](https://pypi.org/project/aea/):

       pip install aea[all]

    Or, if you use `zsh` rather than `bash`:

       pip install "aea[all]"

3. Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

<p align="center">
  <a href="https://www.youtube.com/embed/xpJA4IT5X88">
    <img src="/data/video-aea.png?raw=true" alt="AEA Video" width="70%"/>
  </a>
</p>

## Alternatively: Install from Source

This approach is not recommended!

### Cloning

This repository contains submodules. Clone with recursive strategy:

    git clone https://github.com/fetchai/agents-aea.git --recursive && cd agents-aea

### Dependencies

All python specific framework dependencies are specified in `setup.py` and installed with the framework. All development dependencies are specified in `Pipfile` (and installed via the commands specified in [Preliminaries](#preliminaries)).

You can have more control on the installed dependencies by leveraging the setuptools' extras mechanism. 

### Preliminaries

- Create and launch a virtual environment with Python 3.7 (any Python `>=` 3.6 works):

      pipenv --python 3.7 && pipenv shell

- Install the package from source:

      pip install .[all]

    Or, if you use `zsh` rather than `bash`:

      pip install ".[all]"

- Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

## Contribute

The following dependency is **only relevant if you intend to contribute** to the repository:

- The project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

The following steps are **only relevant if you intend to contribute** to the repository. They are **not required** for agent development.

- To install development dependencies (here optionally skipping `Pipfile.lock` creation):

      pipenv install --dev --skip-lock

- To install the package from source in development mode:

      pip install -e .[all]

    Of, if you use `zsh` rather than `bash`:

      pip install -e ".[all]"

- To run tests:

      tox -e py3.7

- To run linters (code style checks):

      tox -e flake8

- To run static type checks:

      tox -e mypy

- To run black code formatter:

      tox -e black

- To run bandit security checks:

      tox -e bandit

- To start a live-reloading docs server on localhost
	
      mkdocs serve

- To amend the docs, create a new documentation file in `docs/` and add a reference to it in `mkdocs.yml`.

- To fetch/update submodules:

      git submodule sync --recursive && git submodule update --init --recursive

## Cite

If you are using our software in a publication, please 
consider to cite it with the following BibTex entry:

```
@misc{agents-aea,
  Author = {Marco Favorito and David Minarsch and Ali Hosseini and Aristotelis Triantafyllidis and Diarmid Campbell and Oleg Panasevych and Kevin Chen and Yuri Turchenkov and Lokman Rahmani},
  Title = {Autonomous Economic Agent (AEA) Framework},
  Year = {2019},
}
```
