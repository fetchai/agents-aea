#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
Generate all the protocols from their specifications.

This script takes all the protocol specification (scraped from the protocol README)
and calls the `aea generate protocol` command.

Currently, it does a lot of assumptions, and might not be useful for
all use cases. However, with not much work, can be customized to achieve
the desired outcomes.

It requires the `aea` package, `black` and `isort` tools.
"""
import argparse
import logging
import os
import pprint
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
from io import StringIO
from itertools import chain
from operator import methodcaller
from pathlib import Path
from typing import Any, Iterator, List, Match, Optional, Tuple, cast

import semver

from aea.cli.registry.utils import download_file, extract, request_api
from aea.common import JSONLike
from aea.configurations.base import ComponentType, ProtocolConfig, ProtocolSpecification
from aea.configurations.constants import DEFAULT_PROTOCOL_CONFIG_FILE, LIBPROTOC_VERSION
from aea.configurations.data_types import PackageId, PublicId
from aea.configurations.loader import (
    ConfigLoader,
    ConfigLoaders,
    load_component_configuration,
)
from scripts.common import check_working_tree_is_dirty


SPECIFICATION_REGEX = re.compile(r"(---\nname.*\.\.\.)", re.DOTALL)
CUSTOM_TYPE_MODULE_NAME = "custom_types.py"
README_FILENAME = "README.md"
PACKAGES_DIR = Path("packages")
TEST_DATA = Path("tests", "data").absolute()
PROTOCOLS_PLURALS = "protocols"
ROOT_DIR = Path(".").absolute()


def subdirs(path: Path) -> Iterator[Path]:
    """Get subdirectories of a path."""
    return filter(methodcaller("is_dir"), path.iterdir())


def find_protocols_in_local_registry() -> Iterator[Path]:
    """Find all protocols in local registry."""
    authors = subdirs(PACKAGES_DIR)
    component_parents = chain(*map(subdirs, authors))
    protocols_parent = filter(lambda p: p.name == PROTOCOLS_PLURALS, component_parents)
    protocols = chain(*map(subdirs, protocols_parent))
    return map(methodcaller("absolute"), protocols)


def _setup_logger() -> logging.Logger:
    """Set up the logger."""
    FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger_ = logging.getLogger("generate_all_protocols")
    logger_.setLevel(logging.INFO)
    return logger_


logger = _setup_logger()


def log(message: str, level: int = logging.INFO) -> None:
    """Produce a logging message."""
    logger.log(level, message)


def enforce(condition: bool, message: str = "") -> None:
    """Custom assertion."""
    if not condition:
        raise AssertionError(message)


def run_cli(*args: Any, **kwargs: Any) -> None:
    """Run a CLI command."""
    log(f"Calling command {args} with kwargs {kwargs}")
    return_code = subprocess.check_call(args, **kwargs)  # nosec
    enforce(
        return_code == 0,
        f"Return code of {pprint.pformat(args)} is {return_code} != 0.",
    )


def run_aea(*args: Any, **kwargs: Any) -> None:
    """
    Run an AEA command.

    :param args: the AEA command
    :param kwargs: keyword arguments to subprocess function
    :return: None
    """
    run_cli(sys.executable, "-m", "aea.cli", *args, **kwargs)


class AEAProject:
    """A context manager class to create and delete an AEA project."""

    old_cwd: str
    temp_dir: str

    def __init__(self, name: str = "my_aea", parent_dir: Optional[str] = None):
        """
        Initialize an AEA project.

        :param name: the name of the AEA project.
        """
        self.name = name
        self.parent_dir = parent_dir

    def __enter__(self) -> None:
        """Create and enter into the project."""
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(dir=self.parent_dir)
        os.chdir(self.temp_dir)

        run_aea("create", "--local", "--empty", self.name, "--author", "fetchai")
        os.chdir(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit the context manager."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)


def _load_protocol_specification_from_string(
    specification_content: str,
) -> ProtocolSpecification:
    """Load a protocol specification from string."""
    file = StringIO(initial_value=specification_content)
    config_loader = ConfigLoader(
        "protocol-specification_schema.json", ProtocolSpecification
    )
    protocol_spec = config_loader.load_protocol_specification(file)
    return protocol_spec


def _get_protocol_specification_from_readme(package_path: Path) -> str:
    """Get the protocol specification from the package README."""
    log(f"Get protocol specification from README {package_path}")
    readme = package_path / "README.md"
    readme_content = readme.read_text()
    enforce(
        "## Specification" in readme_content,
        f"Cannot find specification section in {package_path}",
    )

    search_result = SPECIFICATION_REGEX.search(readme_content)
    enforce(
        search_result is not None,
        f"Cannot find specification section in README of {package_path}",
    )
    specification_content = cast(Match, search_result).group(0)
    # just for validation of the parsed string
    _load_protocol_specification_from_string(specification_content)
    return specification_content


def _save_specification_in_temporary_file(
    name: str, specification_content: str
) -> None:
    """
    Save the specification in a temporary file.

    :param name: the name of the package.
    :param specification_content: the specification content.
    :return: None
    """
    # here, the cwd is the temporary AEA project
    # hence, we are writing in a temporary directory
    spec_path = Path("..", name + ".yaml")
    log(f"Save specification '{name}' in temporary file {spec_path}")
    spec_path.write_text(specification_content)


def _generate_protocol(package_path: Path) -> None:
    """
    Generate the protocol.

    :param package_path: package to the path.
    :return: None
    """
    cmd = ["generate", "protocol", os.path.join("..", package_path.name) + ".yaml"]
    log(f"Generate the protocol. Command: {pprint.pformat(cmd)}")
    run_aea(*cmd)


def run_isort_and_black(directory: Path, **kwargs: Any) -> None:
    """Run black and isort against a directory."""
    run_cli(
        sys.executable, "-m", "black", "--verbose", str(directory.absolute()), **kwargs,
    )
    run_cli(
        sys.executable,
        "-m",
        "isort",
        "--settings-path",
        "setup.cfg",
        "--verbose",
        str(directory.absolute()),
        **kwargs,
    )


def replace_in_directory(name: str, replacement_pairs: List[Tuple[str, str]]) -> None:
    """
    Replace text in directory.

    :param name: the protocol name.
    :param replacement_pairs: a list of pairs of strings (to_replace, replacement).
    :return: None
    """
    log(f"Replace prefix of import statements in directory '{name}'")
    package_dir = Path(PROTOCOLS_PLURALS, name)
    for submodule in package_dir.rglob("*.py"):
        log(f"Process submodule {submodule.relative_to(package_dir)}")
        for to_replace, replacement in replacement_pairs:
            if to_replace not in submodule.read_text():
                continue
            submodule.write_text(submodule.read_text().replace(to_replace, replacement))


def _fix_generated_protocol(package_path: Path) -> None:
    """
    Fix the generated protocol.

    That means:
    - replacing the prefix of import statements for default protocols;
    - restore the original custom types, if any.
    - copy the README, if any.

    :param package_path: path to the protocol package.
                         Used also to recover the protocol name.
    :return: None
    """
    log(f"Restore original custom types in {package_path}")
    custom_types_module = package_path / CUSTOM_TYPE_MODULE_NAME
    if custom_types_module.exists():
        file_to_replace = Path(
            PROTOCOLS_PLURALS, package_path.name, CUSTOM_TYPE_MODULE_NAME
        )
        file_to_replace.write_text(custom_types_module.read_text())

    package_readme_file = package_path / README_FILENAME
    if package_readme_file.exists():
        log(f"Copy the README {package_readme_file} into the new generated protocol.")
        shutil.copyfile(
            package_readme_file,
            Path(PROTOCOLS_PLURALS, package_path.name, README_FILENAME),
        )


def _update_original_protocol(package_path: Path) -> None:
    """
    Update the original protocol.

    :param package_path: the path to the original package.
                         Used to recover the protocol name.
    :return: None
    """
    log(f"Copy the new protocol into the original directory {package_path}")
    shutil.rmtree(package_path)
    shutil.copytree(Path(PROTOCOLS_PLURALS, package_path.name), package_path)


def _fingerprint_protocol(name: str) -> None:
    """Fingerprint the generated (and modified) protocol."""
    log(f"Fingerprint the generated (and modified) protocol '{name}'")
    protocol_config = load_component_configuration(
        ComponentType.PROTOCOL,
        Path(PROTOCOLS_PLURALS, name),
        skip_consistency_check=True,
    )
    run_aea("fingerprint", "protocol", str(protocol_config.public_id))


def _process_packages_protocol(package_path: Path) -> None:
    """
    Process protocol package from local registry.

    It means:
    - extract protocol specification from README
    - generate the protocol in the current AEA project
    - fix the generated protocol (e.g. import prefixed, custom types, ...)
    - update the original protocol with the newly generated one.

    It assumes the working directory is an AEA project.

    :param package_path: path to the package.
    :return: None
    """
    specification_content = _get_protocol_specification_from_readme(package_path)
    _save_specification_in_temporary_file(package_path.name, specification_content)
    _generate_protocol(package_path)
    _fix_generated_protocol(package_path)
    run_isort_and_black(Path(PROTOCOLS_PLURALS, package_path.name), cwd=str(ROOT_DIR))
    _fingerprint_protocol(package_path.name)
    _update_original_protocol(package_path)


def _check_preliminaries() -> None:
    """Check that the required packages are installed."""
    try:
        import aea  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
    except ModuleNotFoundError:
        enforce(False, "'aea' package not installed.")
    enforce(shutil.which("black") is not None, "black command line tool not found.")
    enforce(shutil.which("isort") is not None, "isort command line tool not found.")
    enforce(shutil.which("protoc") is not None, "protoc command line tool not found.")
    result = subprocess.run(  # nosec
        ["protoc", "--version"], stdout=subprocess.PIPE, check=True
    )
    result_str = result.stdout.decode("utf-8")
    enforce(
        LIBPROTOC_VERSION in result_str,
        f"Invalid version for protoc. Found: {result_str}. Required: {LIBPROTOC_VERSION}.",
    )


def _process_test_protocol(specification: Path, package_path: Path) -> None:
    """
    Process a test protocol.

    :param specification: path to specification.
    :param package_path: the output directory.
    :return: None
    """
    specification_content = specification.read_text()
    _save_specification_in_temporary_file(package_path.name, specification_content)
    _generate_protocol(package_path)
    _fix_generated_protocol(package_path)
    replacements = [
        (
            f"from packages.fetchai.protocols.{package_path.name}",
            f"from tests.data.generator.{package_path.name}",
        )
    ]
    replace_in_directory(package_path.name, replacements)
    run_isort_and_black(Path(PROTOCOLS_PLURALS, package_path.name), cwd=str(ROOT_DIR))
    _fingerprint_protocol(package_path.name)
    _update_original_protocol(package_path)


def download_package(package_id: PackageId, destination_path: str) -> None:
    """Download a package into a directory."""
    api_path = f"/{package_id.package_type.to_plural()}/{package_id.author}/{package_id.name}/{package_id.public_id.LATEST_VERSION}"
    resp = cast(JSONLike, request_api("GET", api_path))
    file_url = cast(str, resp["file"])
    filepath = download_file(file_url, destination_path)
    extract(filepath, destination_path)


def _bump_protocol_specification_id(
    package_path: Path, configuration: ProtocolConfig
) -> None:
    """Bump spec id version."""
    spec_id: PublicId = configuration.protocol_specification_id  # type: ignore
    old_version = semver.VersionInfo.parse(spec_id.version)
    new_version = str(old_version.bump_minor())
    new_spec_id = PublicId(spec_id.author, spec_id.name, new_version)
    configuration.protocol_specification_id = new_spec_id
    with (package_path / DEFAULT_PROTOCOL_CONFIG_FILE).open("w") as file_output:
        ConfigLoaders.from_package_type(configuration.package_type).dump(
            configuration, file_output
        )


def _bump_protocol_specification_id_if_needed(package_path: Path) -> None:
    """
    Check if protocol specification id needs to be bumped.

    Workflow:
    - extract protocol specification file from README
    - download latest protocol id and extract its protocol specification as above
    - if different, bump protocol specification version, else don't.

    :param package_path: path to the protocol package.
    :return: None
    """
    # extract protocol specification file from README
    current_specification_content = _get_protocol_specification_from_readme(
        package_path
    )

    # download latest protocol id and extract its protocol specification as above
    configuration: ProtocolConfig = cast(
        ProtocolConfig,
        load_component_configuration(ComponentType.PROTOCOL, package_path),
    )
    temp_directory = Path(tempfile.mkdtemp())
    download_package(configuration.package_id, str(temp_directory))
    downloaded_package_directory = temp_directory / configuration.name
    old_specification_content = _get_protocol_specification_from_readme(
        downloaded_package_directory
    )
    old_configuration: ProtocolConfig = cast(
        ProtocolConfig,
        load_component_configuration(
            ComponentType.PROTOCOL,
            downloaded_package_directory,
            skip_consistency_check=True,
        ),
    )

    # if different, bump protocol specification version, else don't.
    public_id_version_is_newer = (
        old_configuration.public_id.package_version  # type: ignore
        <= configuration.public_id.package_version
    )
    content_is_different = current_specification_content != old_specification_content
    if public_id_version_is_newer and content_is_different:
        log(
            f"Bumping protocol specification id from '{old_configuration.protocol_specification_id}' to '{configuration.protocol_specification_id}'"
        )
        _bump_protocol_specification_id(package_path, configuration)
        return
    log(
        "Protocol specification id not bumped - content is not different, or version is not newer."
    )


def main() -> None:
    """Run the script."""
    _check_preliminaries()

    all_protocols = list(find_protocols_in_local_registry())

    with AEAProject():
        log("=" * 100)
        _process_test_protocol(
            TEST_DATA / "sample_specification.yaml",
            TEST_DATA / "generator" / "t_protocol",
        )
        log("=" * 100)
        _process_test_protocol(
            TEST_DATA / "sample_specification_no_custom_types.yaml",
            TEST_DATA / "generator" / "t_protocol_no_ct",
        )
        for package_path in all_protocols:
            log("=" * 100)
            log(f"Processing protocol at path {package_path}")
            _bump_protocol_specification_id_if_needed(package_path)
            _process_packages_protocol(package_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("generate_all_protocols")
    parser.add_argument(
        "--check-clean", action="store_true", help="Check if the working tree is clean."
    )
    arguments = parser.parse_args()

    main()

    if arguments.check_clean:
        check_working_tree_is_dirty()
