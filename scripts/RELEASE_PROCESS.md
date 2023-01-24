
# Release Process from develop to main

1. Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit). Make sure you have a clean develop virtual environment.

2. Determine the next AEA version (we use [semantic versioning v 2.0.0][semver]). Create a new release branch named "feature/release-<NEW-VERSION>" (e.g. feature/release-1.0.0). Switch to this branch. Run `python scripts/bump_aea_version.py --new-version <NEW_VERSION>`. Commit if satisfied.

3. Bump plugin versions if necessary by running `python scripts/update_plugin_versions.py --update "<PLUGIN_NAME>,<NEW_VERSION>"`. Commit if satisfied.

4. Check the protocols are up-to-date by running `python scripts/generate_all_protocols.py`. Commit if changes occurred.

5. Bump all the packages to their latest versions by running `python scripts/update_package_versions.py`.

6. Check the package upgrades are correct by running `python scripts/check_packages.py` and `python scripts/check_package_versions_in_docs.py`. Commit if satisfied.

7. Check the docs are up-to-date by running `python scripts/generate_api_docs.py` and `python scripts/check_doc_links.py`. Ensure all API pages are added into `mkdocs.yaml`. Ensure documentation can be built: `make docs`. Commit if satisfied.

8. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

9. Run spell checker `./scripts/spell-check.sh`. Run `pylint --disable all --enable spelling ...`. Commit if required.

10. Open a PR from feature/release-<NEW-VERSION> and merge into develop. 

11. Switch to the develop branch, open a PR from develop to main. If there are failures, fix them in a branch off of develop and merge into develop. Repeat until no failure in the develop to main PR.

12. Release packages into registry: `python scripts/deploy_to_registry.py`. You might have to run the script a few times until all packages are updated due to a specific dependency structure.

13. Merge the develop to main PR.

14. Tag version on main.

15. Pull main, make a clean environment (`make new-env` and `poetry shell`).

16. Create a distribution: `make dist`.

17. Publish to PyPI with twine: `twine upload dist/*`. Optionally, publish to Test-PyPI with twine:
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`.

18. For each plugin: create a distribution (`python3 setup.py bdist_wheel sdist`) then perform step 17.

> Note, the AEA develop docker image is automatically created as part of the CI process in the develop to main PR.

> If something goes wrong and only needs a small fix, do `LAST_VERSION.post1` as version, apply fixes, push again to PyPI.

[semver]: https://semver.org/spec/v2.0.0.html