# Contributing

Contributions to the framework, its plugins, related tools and packages are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

There are various ways to contribute:

- If you need support, want to report a bug or ask for features, you can check the [Issues page](https://github.com/valory-xyz/open-aea/issues) and raise an issue, if applicable.

- If you would like to contribute a bug fix of feature then [submit a Pull request](https://github.com/valory-xyz/open-aea/pulls).

For other kinds of feedback, you can contact one of the
[authors](https://github.com/valory-xyz/open-aea/blob/main/AUTHORS.md) by email.

Before reading on, please have a look at the [code of conduct](https://github.com/valory-xyz/open-aea/blob/main/CODE_OF_CONDUCT.md).

## A few simple rules

- All Pull Requests should be opened against the `develop` branch. Do **not** open a Pull Request against `main`!

- Before working on a feature, reach out to one of the core developers or discuss the feature in an issue. The framework caters a diverse audience and new features require upfront coordination.

- Include unit tests for 100% coverage when you contribute new features, as they help to a) prove that your code works correctly, and b) guard against future breaking changes to lower the maintenance cost.

- Bug fixes also generally require unit tests, because the presence of bugs usually indicates insufficient test coverage.

- Keep API compatibility in mind when you change code in the `aea`. The `aea` has passed version 1.0 and hence cannot make non-backward-compatible API changes without a major release. Reviewers of your pull request will comment on any API compatibility issues.

- When you contribute a new feature to `aea`, the maintenance burden is transferred to the core team. This means that the benefit of the contribution must be compared against the cost of maintaining the feature.

- Where possible, add new functionality via plugins. Currently, CLI and ledger plugins are supported. Furthermore, the `aea` native packages also allow for extensibility.

- All files must include a license header.

- Before committing and opening a PR, run all tests locally. This saves CI hours and ensures you only commit clean code.

## Contributing code

If you have improvements, send us your pull requests!

A team member will be assigned to review your pull requests. All tests are run as part of CI as well as various other checks (linters, static type checkers, security checkers, etc). If there are any problems, feedback is provided via GitHub. Once the pull requests is approved and passes continuous integration checks, you or a team member can merge it.

If you want to contribute, start working through the codebase, navigate to the Github "issues" tab and start looking through interesting issues. If you are not sure of where to start, then start by trying one of the smaller/easier issues here i.e. issues with the "good first issue" label and then take a look at the issues with the "contributions welcome" label. These are issues that we believe are particularly well suited for outside contributions, often because we probably won't get to them right now. If you decide to start on an issue, leave a comment so that other people know that you're working on it. If you want to help out, but not alone, use the issue comment thread to coordinate.

## Development setup

First, setup your environment by either using the `develop-image` or by following these steps:

- The simplest way to get setup for development on the framework is to install Python `>=3.6` and `pipenv`, then run the following:

      make new_env
      pipenv shell

- The project uses [Google Protocol Buffers](https://developers.google.com/protocol-buffers/) compiler for message serialization. A guide on how to install it is found [here](https://fetchai.github.io/oef-sdk-python/user/install.html#protobuf-compiler).

##  For a clean workflow run checks in the following order before pushing the code on a PR

- make clean
- make formatters
- make code-checks
- make security

> Only run following if you have modified a file in `packages/`
- make generators
- make common-checks

> else run
- make check-copyright

> run this after making a commit
- make doc-checks
## Further commands needed during development

We have various commands which are helpful during development.

- For linting and static analysis use:

      make lint
      make static
      make pylint
      make security

- For checking packages integrity:

      make package_checks

- To run tests: `make test`.

- For testing `aea.{SUBMODULE}` with `tests/test_{TESTMODULE}` use:

      make dir={SUBMODULE} tdir={TESTMODULE} test-sub

  e.g.

      make dir=cli tdir=cli test-sub

- When making changes to one of the `packages`, then use `python scripts/generate_ipfs_hashes.py` to generate the latest hashes.

### Go Development

- The `fetchai/p2p_libp2p` package is partially developed in Go.

- To install Go visit the [Golang site](https://golang.org/doc/install).

- We use [`golines`](https://github.com/segmentio/golines) and [`golangci-lint`](https://golangci-lint.run) for linting.

- To run tests, use `go test -p 1 -timeout 0 -count 1 -v ./...` from the root directory of the package. If you experience installation or build issues run `go clean -modcache`.
