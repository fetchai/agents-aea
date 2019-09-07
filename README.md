# agents-aea
A framework for autonomous economic agent (AEA) development


## Dependencies

- All python specific dependencies are specified in the Pipfile (and installed via the commands specified in 'Preliminaries').

## Preliminaries

- Create and launch a virtual environment:

      pipenv --python 3.7 && pipenv shell

- Install the package:

      python setup.py install

## Contribute

The following dependency is only relevant if you intend to contribute to the repository:
- the project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

The following steps are only relevant if you intend to contribute to the repository. They are not required for agent development.

- Clear cache

      pipenv --clear

- Install development dependencies:

	  pipenv install --dev

- Install package in (development mode):

	  pip3 install -e .

- After changes to the protobuf schema run:

	  python setup.py protoc

- To run tests (ensure no oef docker containers are running):

	  tox -e py37

- To run linters (code style checks):

	  tox -e flake8

- To run static type checks:

	  mypy aea tests examples

## Use the `aea` command-line tool

Please check this [README](./aea/cli/README.md) if you want to use the `aea` command-line tool.
