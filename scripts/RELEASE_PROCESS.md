
# Release Process from develop to main

1. Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit). Make sure you have a clean develop virtual environment.

2. Determine the next AEA version
   Create new release branch named "feature/release-{new-version}, switch to this branch"
   Run `python scripts/bump_aea_version.py --new-version NEW_VERSION_HERE`. Commit if satisfied.

3. Bump plugin versions if necessary by running `python scripts/update_plugin_versions.py --update "PLUGIN_NAME,NEW_VERSION"`. Commit if satisfied.

4. Check the protocols are up-to-date by running `aea generate-all-protocols --check-clean`. Commit if changes occurred. Do the same for test protocols using `aea generate-all-protocols tests/data/packages --check-clean`

5. [CURRENTLY SKIPPED] Bump all the packages to their latest versions by running `python scripts/update_package_versions.py`.

6. Update the package and dependency hashes using `make hashes`. Commit if changes occurred.

7. Check the package upgrades are correct by running `python -m aea.cli check-packages` and `python scripts/check_package_versions_in_docs.py`. Commit if satisfied.

8. Check the docs are up-to-date by running `tox -e generate-api-documentation`, `python scripts/check_doc_ipfs_hashes.py --fix` and `python scripts/check_doc_links.py`. Ensure all links are configured `mkdocs serve`. Commit if satisfied.

9. Ensure the signing protocol hash in open-aea is updated: `tests/test_configurations/test_constants.py::test_signing_protocol_hash`

10. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

11. Run spell checker `./scripts/spell-check.sh`. Run `pylint --disable all --enable spelling ...`. Commit if required.

12. Open PRs and merge into develop. Then open develop to main PR and merge it.

13. Tag version on main.

14. Pull main, make a clean environment (`pipenv --rm` and `pipenv --python 3.10` and `pipenv shell`) and create distributions: `make dist`.

15. Publish to PyPI with twine: `pip install twine` and `twine upload dist/*`. Optionally, publish to Test-PyPI with twine:
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`.

16. Repeat 14. & 15. for each plugin (use `python setup.py sdist bdist_wheel` instead of `make dist`).

17. Make clean environment and install release from PyPI: `pip install open-aea[all] --no-cache`.

18. Publish the latest packages to the IPFS registry using `aea init --reset --author valory --ipfs --remote` and `aea push-all`. If necessary, run it several times until all packages are updated.

19. Build the release images using `skaffold build -p release` which will also publish them to Docker Hub. This builds with no cache so to ensure replicable builds.

20. Tag the latest images using `skaffold build -p release-latest` which will also publish them to Docker Hub.


If something goes wrong and only needs a small fix do `LAST_VERSION.post1` as version, apply fixes, push again to PyPI.
