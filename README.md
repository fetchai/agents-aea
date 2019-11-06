# agents-aea
A framework for autonomous economic agent (AEA) development

## Get started

- Create and launch a virtual environment with Python 3.7:

      pipenv --python 3.7 && pipenv shell

- Install the package from [pypi](https://pypi.org/project/aea/):


      pip install aea[all]


- Then, build your agent as described in the [docs](https://fetchai.github.io/agents-aea/).

## Alternatively: Install from Source

### Cloning

This repository contains submodules. Clone with recursive strategy:

	  git clone https://github.com/fetchai/agents-aea.git --recursive && cd agents-aea

### Dependencies

All python specific dependencies are specified in the Pipfile (and installed via the commands specified in 'Preliminaries').

Or, you can have more control on the installed dependencies by leveraging the setuptools' extras mechanism (more details later). 

### Preliminaries

- Create and launch a virtual environment:

      pipenv --python 3.7 && pipenv shell

- Install the package from source:

      pip install .[all]

- To install only specific extra dependencies, e.g. `cli`:

      pip install .[cli]

### Contribute

The following dependency is only relevant if you intend to contribute to the repository:
- the project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

The following steps are only relevant if you intend to contribute to the repository. They are not required for agent development.

- Install development dependencies:

	  pipenv install --dev

- Install package in (development mode):

	  pip install -e .

- After changes to the protobuf schema run:

	  python setup.py protoc

- To run tests (ensure no oef docker containers are running):

	  tox -e py37

- To run linters (code style checks):

	  tox -e flake8

- To run static type checks:

	  tox -e mypy

- Docs:

	* `mkdocs serve` - Start the live-reloading docs server on localhost.

To amend the docs, create a new documentation file in `docs/` and add a reference to it in `mkdocs.yml`.
