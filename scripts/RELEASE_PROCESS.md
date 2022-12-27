
# Release Process from develop to main

1. Make sure you have a clean develop virtual environment (`make new_env`). Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit after running `make formatters`, `make code-checks` and `make generators`).

2. Determine the next AEA version: Create new release branch named "feature/release-{new-version}, switch to this branch and run `python scripts/bump_aea_version.py --new-version NEW_VERSION_HERE`. Commit if satisfied.

3. Bump plugin versions if necessary by running `python scripts/update_plugin_versions.py --update "PLUGIN_NAME,NEW_VERSION"`. Commit if satisfied.

4. [CURRENTLY SKIPPED] Bump all the packages to their latest versions by running `python scripts/update_package_versions.py`.

5. Update the package and dependency hashes, protocols, as well as docs using `make generators`. Commit if changes occurred.

6. Ensure all links are configured `tox -e docs-serve`. Commit if satisfied.

7. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

8. Run spell checker `./scripts/spell-check.sh`. Run `pylint --disable all --enable spelling ...`. Commit if required.

9. Open PRs and merge into develop. Then open develop to main PR and merge it.

10. Tag version on main.

11. Pull main, make a clean environment (`pipenv --rm` and `pipenv --python 3.10` and `pipenv shell`) and create distributions: `make dist`.

12. Publish to PyPI with twine: `pip install twine` and `twine upload dist/*`. Optionally, publish to Test-PyPI with twine:
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`.

13. Repeat 14. & 15. for each plugin (use `python setup.py sdist bdist_wheel` instead of `make dist`).

14. Make clean environment and install release from PyPI: `pip install open-aea[all] --no-cache`.

15. Publish the latest packages to the IPFS registry using `aea init --reset --author valory --ipfs --remote` and `aea push-all`. If necessary, run it several times until all packages are updated.

16. Build the release images using `skaffold build -p release` which will also publish them to Docker Hub. This builds with no cache so to ensure replicable builds.

17. Tag the latest images using `skaffold build -p release-latest` which will also publish them to Docker Hub.


If something goes wrong and only needs a small fix do `LAST_VERSION.post1` as version, apply fixes, push again to PyPI.
