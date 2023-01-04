# Development Guidelines

- [Getting the Source](#get)
- [Setting up a New Development Environment](#setup)
- [Development](#dev)
  - [General code quality checks](#general)
  - [Updating API documentation](#api)
  - [Updating documentation](#docs)
  - [Updating dependencies](#deps)
  - [Updating packages](#package)
  - [Tests](#tests)
  - [Miscellaneous checks](#misc)
- [Contributing](#contributing)
- [Making Releases](#release)

## <a name="get"></a> Getting the Source

1. Fork the [agents-aea repository][repo]. 
2. Clone your fork of the agents-aea repository:
   ```shell
   git clone git@github.com:<github username>/agents-aea.git
   ```
3. Define an `upstream` remote pointing back to the main agents-aea repository:
   ```shell
   git remote add upstream https://github.com/fetchai/agents-aea.git
   ```

## <a name="setup"></a> Setting up a New Development Environment:

1. Ensure you have Python (version `3.8`, `3.9` or `3.10`) and [`poetry`][poetry]. 
2.     make new-env
   This will create a new virtual environment using poetry with the project and all the development dependencies installed. 
3.     poetry shell
    To enter the virtual environment. 

Depending on what you want to do, you might need extra tools on your system:

- The project uses [Google Protocol Buffers][protobuf] compiler for message serialization. The compiler's version must match the `protobuf` library installed with the project (see `pyproject.toml`).  
- The `fetchai/p2p_libp2p` package is partially developed in Go. To make changes, [install Golang][go].
- To update fingerprint hashes of packages, you will need the [IPFS daemon][ipfs]. 

## <a name="dev"></a>Development

### <a name="general"></a>General code quality checks
To run general code quality checkers, formatters and linters:
-     make lint
  Automatically formats your code and sorts your imports, checks your code's quality and scans for any unused code.
-     make mypy
  Statically checks the correctness of the types.
-     make pylint
  Analyses the quality of your code.
-     make security
  Checks the code for known vulnerabilities and common security issues.
-     make clean
  Cleans your development environment and deletes temporary files and directories.
- For the Go parts, we use [`golines`][golines] and [`golangci-lint`][golangci-lint] for linting.

### <a name="docs"></a>Updating documentation
We use [`mkdocs`][mkdocs] and [`material-for-mkdocs`][material] for static documentation pages. To make changes to the documentation:
-     make docs-live
  This starts a live-reloading docs server on localhost which you can access by going to http://127.0.0.1:8000/ in your browser. Making changes to the documentation automatically reloads this page, showing you the latest changes. 

  To create a new documentation page, add a markdown file under `/docs/` and add a reference to this page in `mkdocs.yml` under `nav`.

### <a name="api"></a>Updating API documentation
If you've made changes to the core `aea` package that affects the public API:
-     make generate-api-docs
  This regenerates the API docs. If pages are added/deleted, or there are changes in their structure, these need to be reflected manually in the `nav` section of `mkdocs.yaml`.

### <a name="deps"></a>Updating dependencies
We use [`poetry`][poetry] and `pyproject.toml` to manage the project's dependencies. 

If you've made any changes to the dependencies (e.g. added/removed dependencies, or updated package version requirements):
-     poetry lock
  This re-locks the dependencies. Ensure that the `poetry.lock` file is pushed into the repository (by default it is).
-     make liccheck
  Checks that the licence for the framework is correct, taking into account the licences for all dependencies, their dependencies and so forth.

### <a name="package"></a>Updating packages
If you've made changes to the packages included in the repository (e.g. skills, protocols, connections, contracts):
-     make update-package-hashes
  Updates the fingerprint hashes of every package in the repository.
-     make package-checks
  Checks, a) that the package hashes are correct, b) the documentation correctly references the latest packages, and c) runs other correctness checks on packages.

### <a name="tests"></a>Tests
To test the Python part of the project, we use `pytest`. To run the tests:

-     make test 
  Runs all the tests.
-     make test-plugins 
  Runs all plugin tests.
-     make dir={SUBMODULE} tdir={TESTMODULE} test-sub
  Runs the tests for `aea.{SUBMODULE}`. For example, to run the tests for the CLI: `make dir=cli tdir=cli test-sub`

To test the Go parts of the project: 
-     go test -p 1 -timeout 0 -count 1 -v ./...
  from the root directory of a Go package (e.g. `fetchai/p2p_libp2p`) to run the Golang tests. 
  If you experience installation or build issues, run `go clean -modcache`.

### <a name="misc"></a>Miscellaneous checks
-     copyright-check
  Checks that all files have the correct copyright header (where applicable).
-     check-doc-links
  Checks that the links in the documentations are valid and alive.
-     make libp2p-diffs
  Checks the libp2p code under `libs` and in the connection packages aren't different.
-     make plugin-diffs
  Checks the plugin licenses and the codes under `cosmos` and `fetchai` ledger plugins aren't different.

## <a name="contributing"></a>Contributing

For instructions on how to contribute to the project (e.g. creating Pull Requests, commit message convention, etc), see the [contributing guide][contributing guide].

## <a name="release"></a>Making Releases

For instructions on how to make a release, see the [release process][release process] guide.

[protobuf]: https://developers.google.com/protocol-buffers/
[ipfs]: https://docs.ipfs.tech/install/
[go]: https://golang.org/doc/install
[golines]: https://github.com/segmentio/golines
[golangci-lint]: https://golangci-lint.run
[mkdocs]: https://www.mkdocs.org
[material]: https://squidfunk.github.io/mkdocs-material/
[poetry]: https://python-poetry.org
[contributing guide]: https://github.com/fetchai/agents-aea/blob/main/CONTRIBUTING.md
[release process]: https://github.com/fetchai/agents-aea/blob/main/scripts/RELEASE_PROCESS.md
[repo]: https://github.com/fetchai/agents-aea