## Proposed changes

Describe the big picture of your changes here to communicate to the maintainers why we should accept this pull request.

## Fixes

If it fixes a bug or resolves a feature request, be sure to link to that issue.

## Types of changes

What types of changes does your code introduce to agents-aea?
_Put an `x` in the boxes that apply_

- [ ] Bugfix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)

## Checklist

_Put an `x` in the boxes that apply._

- [ ] I have read the [CONTRIBUTING](../CONTRIBUTING.md) doc
- [ ] I am making a pull request against the `develop` branch (left side). Also you should start your branch off our `develop`.
- [ ] Lint and unit tests pass locally with my changes
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] I have checked that code coverage does not decrease.
- [ ] I have checked that the documentation about the `aea cli` tool works
- [ ] I have added necessary documentation (if appropriate)
- [ ] Any dependent changes have been merged and published in downstream modules

## Further comments

If this is a relatively large or complex change, kick off the discussion by explaining why you chose the solution you did and what alternatives you considered, etc...


DELETE INCLUSIVE THIS AND BELOW FOR STANDARD PR
------

## Release summary

Version number: [e.g. 1.0.1]

## Release details

Describe in short the main changes with the new release.

## Checklist

_Put an `x` in the boxes that apply._

- [ ] I have read the [CONTRIBUTING](../CONTRIBUTING.md) doc
- [ ] I am making a pull request against the `master` branch (left side), from `develop`
- [ ] Lint and unit tests pass locally
- [ ] I have checked the fingerprint hashes are correct by running (`scripts/generate_ipfs_hashes.py`)
- [ ] I have regenerated the latest API docs
- [ ] I built the documentation and updated it with the latest changes
- [ ] I have added an item in `HISTORY.md` for this release
- [ ] I bumped the version number in the `aea/__version__.py` file.
- [ ] I bumped the version number in the `docs/version.md` file
- [ ] I bumped the version number in every Docker image of the repo and published it. Also, I built and published them with tag `latest`  
      (check the READMEs of [`aea-develop`](../develop-image/README.md#publish) 
      and [`aea-deploy`](../deploy-image/README.md#publish))
- [ ] I have checked that the documentation about the `aea cli` tool works
- [ ] I have pushed the latest packages to the registry.

## Further comments

Write here any other comment about the release, if any.
