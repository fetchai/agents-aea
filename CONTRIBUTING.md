# Contributing

Contributions to the framework, plugins, packages and related tools are welcome. As a contributor, here are the guidelines we would like you to follow:

- [Code of Conduct](#coc)
- [Question or Problem?](#question)
- [Issues and Bugs](#issue)
- [Feature Requests](#feature)
- [Submission Guidelines](#submit)
- [Coding Rules](#rules)
- [Commit Message Guidelines](#commit)

## <a name="coc"></a> Code of Conduct

Please read and follow our [Code of Conduct][coc].

## <a name="question"></a> Question or Problem?

Please use [Github Discussions][ghdiscussion] for support related questions and general discussions. Do NOT open issues as they are for bug reports and feature requests. This is because:

- Questions and answers stay available for public viewing so your question/answer might help someone else.
- Github Discussions voting system ensures the best answers are prominently visible.

## <a name="issue"></a> Found a Bug?

If you find a bug in the source code [submit a bug report issue](#submit-issue) to our [GitHub repository][github].
Even better, you can [submit a Pull Request](#submit-pr) with a fix.

## <a name="feature"></a> Missing a Feature?
You can *request* a new feature by [submitting a feature request issue](#submit-issue) to our [GitHub repository][github].
If you would like to *implement* a new feature:

* For a **Major Feature**, first open an issue and outline your proposal so that it can be discussed.
* **Small Features** can be crafted and directly [submitted as a Pull Request](#submit-pr).

## <a name="submit"></a> Submission Guidelines

### <a name="submit-issue"></a> Submitting an Issue

Before you submit an issue, please search the [issue tracker][issues]. An issue for your problem might already exist and the discussion might inform you of workarounds readily available.

For bug reports, it is important that we can reproduce and confirm it. For this, we need you to provide a minimal reproduction instruction (this is part of the bug report issue template).

You can file new issues by selecting from our [new issue templates](https://github.com/fetchai/agents-aea/issues/new/choose) and filling out the issue template.

### <a name="submit-pr"></a> Submitting a Pull Request (PR)

Before you submit your Pull Request (PR) consider the following guidelines:

1. All Pull Requests should be based off of and opened against the `develop` branch. Do **not** open a Pull Request against `main`!

2. Search [Existing PRs](https://github.com/fetchai/agents-aea/pulls) for an open or closed PR that relates to your submission.
   You don't want to duplicate existing efforts.

3. Be sure that an issue exists describing the problem you're fixing, or the design for the feature you'd like to add.

4. [Fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) the [repository][github].

5. In your forked repository, make your changes in a new git branch created from the `develop` branch.

6. Make your changes, **including test cases** and updating documentation where appropriate.

7. Follow our [coding rules](#rules).

8. Run all tests and checks locally, as described in the [development guide](#dev), and ensure they pass. This saves CI hours and ensures you only commit clean code.

9. Commit your changes using a descriptive commit message that follows our [commit message conventions](#commit).

10. Push your branch to GitHub.

11. In GitHub, send a pull request to `fetchai:develop`.

> Where possible, try to take advantage of the modularity of the framework and add new functionality via a new module. Currently, ledger plugins are supported and packages (skills, connections, protocols, contracts) allow for extensibility.

#### Reviewing a Pull Request

The AEA team reserves the right not to accept pull requests from community members who haven't been good citizens of the community. Such behavior includes not following our [code of conduct][coc] and applies within or outside of the managed channels.

When you contribute a new feature, the maintenance burden is transferred to the core team. This means that the benefit of the contribution must be compared against the cost of maintaining the feature.

#### Addressing review feedback

If we ask for changes via code reviews then:

1. Make the required updates to the code.

2. Re-run the tests and checks to ensure they are still passing.

3. Create a new commit and push to your GitHub repository (this will update your Pull Request).

#### After your pull request is merged

After your pull request is merged, you can safely delete your branch and pull the changes from the (upstream) repository.

## <a name="rules"></a> Coding Rules
To ensure consistency throughout the source code, keep these rules in mind as you are working:

* All code must pass our code quality checks (linters, formatters, etc). See the [development guide](#dev) section for more detail.
* All features or bug fixes **must be tested** via unit-tests and if applicable integration-tests. These help to, a) prove that your code works correctly, and b) guard against future breaking changes and lower the maintenance cost.
* All public features **must be documented**.
* All files must include a license header.

## <a name="commit"></a> Commit Message Format

Please follow the [Conventional Commits v1.0.0][convcommit]. The commit types must be one of the following:

* **build**: Changes that affect the build system or external dependencies
* **ci**: Changes to our CI configuration files and scripts
* **docs**: Documentation only changes
* **feat**: A new feature
* **fix**: A bug fix
* **perf**: A code change that improves performance
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **test**: Adding missing tests or correcting existing tests

[coc]: https://github.com/fetchai/agents-aea/blob/main/CODE_OF_CONDUCT.md
[ghdiscussion]: https://github.com/fetchai/agents-aea/discussions
[issues]: https://github.com/fetchai/agents-aea/issues
[convcommit]: https://www.conventionalcommits.org/en/v1.0.0/
[dev-doc]: https://github.com/angular/angular/blob/main/docs/DEVELOPER.md
[github]: https://github.com/fetchai/agents-aea
[discord]: https://bit.ly/3ra5uMI