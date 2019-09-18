# agents-aea
A framework for autonomous economic agent (AEA) development

## Get started

First, install the package from [test-pypi](https://test.pypi.org/project/aea/):

`
pip install cryptography base58
pip install -i https://test.pypi.org/simple/ aea
`

Then, build your agent as described in the [AEA CLI readme](../master/aea/cli/README.md)

## Dependencies

All python specific dependencies are specified in the Pipfile (and installed via the commands specified in 'Preliminaries').

Or, you can have more control on the installed dependencies by leveraging the setuptools' extras mechanism (more details later). 

## Preliminaries

- Create and launch a virtual environment:

      pipenv --python 3.7 && pipenv shell

- Install the package from source:

      pip install .[all]

- To install only specific extra dependencies, e.g. `cli` and `oef-protocol`:

      pip install .[cli,oef-channel]

## Contribute

The following dependency is only relevant if you intend to contribute to the repository:
- the project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

The following steps are only relevant if you intend to contribute to the repository. They are not required for agent development.

- Clear cache

      pipenv --clear

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

	* `mkdocs serve` - Start the live-reloading docs server.
	* `mkdocs build --clean` - Build the documentation site.
