# agents-aea
A framework for autonomous economic agent (AEA) development

## Get started

1. Create and launch a clean virtual environment with Python 3.7 (any Python `>=` 3.6 works):

        pipenv --python 3.7 && pipenv shell

2. Install the package from [PyPI](https://pypi.org/project/aea/):


        pip install aea[all]


3. Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

<p align="center">
  <img src="https://github.com/fetchai/agents-aea/blob/develop/data/aea.png?raw=true" alt="AEA" width="70%"/>
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

- Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

## Contribute

The following dependency is **only relevant if you intend to contribute** to the repository:
- the project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

The following steps are only relevant if you intend to contribute to the repository. They are not required for agent development.

- Install development dependencies (optionally skipping Lockfile creation):

	  pipenv install --dev --skip-lock

- Install package in development mode (this step replaces `pip install aea[all]` above):

	  pip install -e .

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

- Docs:

	* `mkdocs serve` - Start the live-reloading docs server on localhost.

To amend the docs, create a new documentation file in `docs/` and add a reference to it in `mkdocs.yml`.

- Fetch submodules:

	  git submodule sync --recursive && git submodule update --init --recursive
