<h1 align="center">
    <b>AEA Framework</b>
</h1>

<p align="center">
  <a href="https://pypi.org/project/aea/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/aea">
  </a>
  <a href="https://pypi.org/project/aea/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/aea">
  </a>
  <a>
    <img alt="PyPI - Wheel" src="https://img.shields.io/pypi/wheel/aea">
  </a>
  <a href="https://github.com/fetchai/agents-aea/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/pypi/l/aea"> 
  </a>
  <a href="https://pypi.org/project/aea/">
    <img alt="License" src="https://img.shields.io/pypi/dm/aea"> 
  </a>
  <a href="https://fetch-ai.slack.com/join/shared_invite/enQtNDI2MDYwMjE3OTQwLWY0ZjAyYjM0NGQzNWRhNDMxMzdjYmVhYTE3NDNhNTAyMTE0YWRkY2VmOWRmMGQ3ODM1N2NjOWUwNDExM2U3YjY">
    <img alt="Slack" src="https://img.shields.io/badge/slack-fetchai-purple.svg">
  </a>
</p>
<p align="center">
  <a href="https://github.com/fetchai/agents-aea/workflows/AEA%20framework%20sanity%20checks%20and%20tests">
    <img alt="AEA framework sanity checks and tests" src="https://github.com/fetchai/agents-aea/workflows/AEA%20framework%20sanity%20checks%20and%20tests/badge.svg?branch=main">
  </a>
  <a href="">
    <img alt="Codecov" src="https://img.shields.io/codecov/c/github/fetchai/agents-aea">
  </a>
  <a href="https://img.shields.io/badge/lint-flake8-blueviolet">
    <img alt="flake8" src="https://img.shields.io/badge/lint-flake8-yellow" >
  </a>
  <a href="https://github.com/python/mypy">
    <img alt="mypy" src="https://img.shields.io/badge/static%20check-mypy-blue">
  </a>
  <a href="https://github.com/psf/black">
    <img alt="Black" src="https://img.shields.io/badge/code%20style-black-black">
  </a>
  <a href="https://github.com/PyCQA/bandit">
    <img alt="mypy" src="https://img.shields.io/badge/security-bandit-lightgrey">
  </a>
</p>

<p align="center">
A framework for autonomous economic agent (AEA) development
</p>

<p align="center">
  <img src="/data/aea.png?raw=true" alt="AEA Description" width="70%"/>
</p>

## Get started developing AEAs

1. Create and launch a clean virtual environment with Python 3.7 (any Python `>=` 3.6 works):

       pipenv --python 3.7 && pipenv shell

2. Install the package from [PyPI](https://pypi.org/project/aea/):

       pip install aea[all]

    Or, if you use `zsh` rather than `bash`:

       pip install "aea[all]"

3. Then, build your agent as described in the [docs](https://docs.fetch.ai/aea/).

<p align="center">
  <a href="https://www.youtube.com/embed/xpJA4IT5X88">
    <img src="/data/video-aea.png?raw=true" alt="AEA Video" width="70%"/>
  </a>
</p>

## Alternatively (1): Use `pipx` (CLI usage only)

1. Install [pipx](https://github.com/pipxproject/pipx)

2. Install the package from [PyPI](https://pypi.org/project/aea/):

       pipx install aea[all]

3. Run AEA CLI e.g.:

       aea --help

## Alternatively (2): Install from Source

This approach is not recommended!

### Cloning

This repository contains submodules. Clone with recursive strategy:

    git clone https://github.com/fetchai/agents-aea.git --recursive && cd agents-aea

- To fetch/update submodules (for existing local repo):

      git submodule sync --recursive && git submodule update --init --recursive

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

## Documentation

- All documentation is hosted [here](https://docs.fetch.ai/aea).

- To start a live-reloading docs server on localhost: `mkdocs serve`. To amend the docs, create a new documentation file in `docs/` and add a reference to it in `mkdocs.yml`.

- To run demos against local packages use flag `--local` in `aea` CLI commands.

## Contributing

We welcome contributions to the framework, its plugins, related tools and packages. Please consult the [contributing guide](https://github.com/fetchai/agents-aea/blob/main/CONTRIBUTING.md) for details.

## Cite

If you are using our software in a publication, please 
consider to cite it with the following BibTex entry:

```
@misc{agents-aea,
  Author = {Marco Favorito and David Minarsch and Ali Hosseini and Aristotelis Triantafyllidis and Diarmid Campbell and Oleg Panasevych and Kevin Chen and Yuri Turchenkov and Lokman Rahmani and Jiří Vestfál and James Riehl},
  Title = {Autonomous Economic Agent (AEA) Framework},
  Year = {2019},
}
```
