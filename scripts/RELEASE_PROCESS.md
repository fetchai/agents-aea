
# Release Process from develop to master

1. Make sure all tests pass, coverage is at 100% and the local branch is in a clean state (nothing to commit). Make sure you have a clean develop virtual environment.

2. Determine the next AEA version and run `python scripts/bump_aea_version.py --new-version NEW_VERSION_HERE`. Commit if satisfied.

3. Check the protocols are up-to-date by running `python scripts/generate_all_protocols.py`. Commit if changes occured.

4. Bump all the packages to their latest versions by running `python scripts/update_package_versions.py`.

5. Check the package upgrades are correct by running `python scripts/check_package_dependencies.py` and `python scripts/check_package_versions_in_docs.py`. Commit if satisfied.

6. Check the docs are up-to-date by running `python scripts/generate_api_docs.py` and `python scripts/check_doc_links.py`. Ensure all links are configured `mkdocs serve`. Commit if satisfied.

7. Write release notes and place them in `HISTORY.md`. Add upgrading tips in `upgrading.md`. Commit if satisfied.

8. Open PRs and merge into master.

9. Tag version on master.

10. Pull master, make a clean environment and create distributions: `python setup.py sdist bdist_wheel`.

11. Publish to pypi with twine: `twine upload dist/*`. Optionally, publish to test-pypi with twine:
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`.

12. Make clean environment and install release from PyPI: `pip install aea[all] --no-cache`.

13. Release packages into registry: `python scripts/deploy_to_registry.py`.

14. If necessary, adjust version references in `SECURITY.md`. Commit if satisfied.

If something goes wrong and only needs a small fix do `LAST_VERSION.post1` as version, apply fixes, push again to PyPI.
