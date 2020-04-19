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
  <img src="https://github.com/fetchai/agents-aea/blob/develop/data/aea.png?raw=true" alt="AEA" width="70%"/>
</p>

## Get started

1. Create and launch a clean virtual environment with Python 3.7 (any Python `>=` 3.6 works):

       pipenv --python 3.7 && pipenv shell

2. Install the package from [PyPI](https://pypi.org/project/aea/):

       pip install aea[all]

    or is you use `zsh` rather than `bash`:

       pip install "aea[all]"

3. Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

<p align="center">
  <iframe width="560" height="315" src="https://www.youtube.com/embed/xpJA4IT5X88" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</p>

## Alternatively: Install from Source

### Cloning

This repository contains submodules. Clone with recursive strategy:

    git clone https://github.com/fetchai/agents-aea.git --recursive && cd agents-aea

### Dependencies

All python specific dependencies are specified in the Pipfile (and installed via the commands specified in 'Preliminaries').

Or, you can have more control on the installed dependencies by leveraging the setuptools' extras mechanism (more details later). 

### Preliminaries

- Create and launch a virtual environment with Python 3.7 (any Python `>=` 3.6 works):

      pipenv --python 3.7 && pipenv shell

- Install the package from source:

      pip install .[all]

    or is you use `zsh` rather than `bash`:

      pip install ".[all]"

- Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

## Contribute

The following dependency is **only relevant if you intend to contribute** to the repository:

- The project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

The following steps are only relevant if you intend to contribute to the repository. They are not required for agent development.

- Install development dependencies (optionally skipping Lockfile creation):

      pipenv install --dev --skip-lock

- Install package in development mode (this step replaces `pip install aea[all]` above):

      pip install -e .[all]

    (`pip install -e ".[all]"` if you use `zsh` rather than `bash`.)

- To run tests (ensure no oef docker containers are running):

      tox -e py3.7

- To run linters (code style checks):

      tox -e flake8

- To run static type checks:

      tox -e mypy

- To run black code formatter:

      tox -e black

- To run bandit security checks:

      tox -e bandit-main
      tox -e bandit-tests

- To start a live-reloading docs server on localhost
	
      mkdocs serve

- To amend the docs, create a new documentation file in `docs/` and add a reference to it in `mkdocs.yml`.

- Fetch submodules:

      git submodule sync --recursive && git submodule update --init --recursive

## Cite

If you are using our software in a publication, please 
consider to cite it with the following BibTex entry:

```
@misc{agents-aea,
  Author = {Marco Favorito and David Minarsch and Ali Hosseini and Aristotelis Triantafyllidis and Diarmid Campbell and Oleg Panasevych and Kevin Chen},
  Title = {Autonomous Economic Agent (AEA) Framework},
  Year = {2019},
}
```
