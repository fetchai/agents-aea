## Proposed changes

Describe the changes here.

## Issues

Links to any issues resolved.

## Types of changes

What types of changes does your code introduce to agents-aea?
_Put an `x` in the boxes that apply_

- [ ] Bugfix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to stop working as expected)
- [ ] Something else (e.g. test, package, script, example, deployment, infrastructure, ...)

## Checklist

_Put an `x` in the boxes that apply._

- [ ] I have based my branch, and I am making a pull request against, the `develop` branch.
- [ ] Lint and unit tests pass locally with my changes.
- [ ] I have added tests that prove my fix is effective or that my feature works.
- [ ] I have checked that code coverage does not decrease.
- [ ] I have added/updated the documentations (if applicable).
- [ ] Any dependent changes have been merged and published in downstream modules.

## Further comments

If this is a relatively large or complex change, kick off the discussion by explaining why you chose the solution you did, what alternatives you considered, etc.


DELETE INCLUSIVE THIS AND BELOW FOR STANDARD PR
------

## Release summary

Version number: [e.g. 1.0.1]

## Release details

Describe in short the main changes with the new release.

## Checklist

_Put an `x` in the boxes that apply._

- [ ] I am making a pull request against the `main` branch from `develop`.
- [ ] Lint and unit tests pass locally.
- [ ] I have checked the fingerprint hashes are correct by running (`scripts/generate_ipfs_hashes.py`).
- [ ] I have regenerated and updated the latest API docs.
- [ ] I built the documentation and updated it with the latest changes.
- [ ] I have added an item in `HISTORY.md` for this release.
- [ ] I bumped the version number in the `aea/__version__.py` file.
- [ ] I bumped the version number in every Docker image of the repo and published it. Also, I built and published them with tag `latest`  
      (check the READMEs of [`aea-develop`](https://github.com/fetchai/agents-aea/blob/master/develop-image/README.md#publish) 
      and [`aea-user`](https://github.com/fetchai/agents-aea/blob/master/develop-image/user-image/README.md#publish))
- [ ] I have pushed the latest packages to the registry.
- [ ] I have uploaded the latest `aea` to PyPI.
- [ ] I have uploaded the latest plugins to PyPI.

## Further comments

Write here any other comment about the release, if any.
