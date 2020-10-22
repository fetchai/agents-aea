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

import logging
import operator
import os
import pprint
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Match, Optional, cast

from aea.configurations.base import ComponentType, ProtocolSpecification
from aea.configurations.loader import ConfigLoader, load_component_configuration


SPECIFICATION_REGEX = re.compile(r"(---\nname.*\.\.\.)", re.DOTALL)
CUSTOM_TYPE_MODULE_NAME = "custom_types.py"
README_FILENAME = "README.md"

PROTOCOL_PATHS = list(
    map(
        operator.methodcaller("absolute"),
        [
            Path("packages", "fetchai", "protocols", "default"),
            Path("packages", "fetchai", "protocols", "signing"),
            Path("packages", "fetchai", "protocols", "state_update"),
            Path("packages", "fetchai", "protocols", "contract_api"),
            Path("packages", "fetchai", "protocols", "fipa"),
            Path("packages", "fetchai", "protocols", "gym"),
            Path("packages", "fetchai", "protocols", "http"),
            Path("packages", "fetchai", "protocols", "ledger_api"),
            Path("packages", "fetchai", "protocols", "ml_trade"),
            Path("packages", "fetchai", "protocols", "oef_search"),
            Path("packages", "fetchai", "protocols", "tac"),
            Path("packages", "fetchai", "protocols", "register"),
        ],
    )
)


def _setup_logger() -> logging.Logger:
    """Set up the logger."""
    FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger_ = logging.getLogger("generate_all_protocols")
    logger_.setLevel(logging.INFO)
    return logger_


logger = _setup_logger()


def log(message: str, level: int = logging.INFO):
    """Produce a logging message."""
    logger.log(level, message)


def enforce(condition, message=""):
    """Custom assertion."""
    if not condition:
        raise AssertionError(message)


def run_cli(*args, **kwargs):
    """Run a CLI command."""
    return_code = subprocess.check_call(args, **kwargs)  # nosec
    enforce(
        return_code == 0,
        f"Return code of {pprint.pformat(args)} is {return_code} != 0.",
    )


def run_aea(*args, **kwargs) -> None:
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

    def __enter__(self):
        """Create and enter into the project."""
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(dir=self.parent_dir)
        os.chdir(self.temp_dir)

        run_aea("create", "--local", "--empty", self.name, "--author", "fetchai")
        os.chdir(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
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


def _save_specification_in_temporary_file(name: str, specification_content: str):
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


def replace_in_directory(name: str):
    """
    Replace text in directory.

    :param name: the protocol name.
    :return: None
    """
    log(f"Replace prefix of import statements in directory '{name}'")
    replace_replacement_pairs = [
        (f"from packages.fetchai.protocols.{name}", f"from aea.protocols.{name}"),
    ]
    package_dir = Path("protocols", name)
    for submodule in package_dir.rglob("*.py"):
        log(f"Process submodule {submodule.relative_to(package_dir)}")
        for to_replace, replacement in replace_replacement_pairs:
            if to_replace not in submodule.read_text():
                continue
            submodule.write_text(submodule.read_text().replace(to_replace, replacement))
            run_cli("isort", str(submodule))
            run_cli("black", str(submodule))


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
        file_to_replace = Path("protocols", package_path.name, CUSTOM_TYPE_MODULE_NAME)
        file_to_replace.write_text(custom_types_module.read_text())

    # if it is a library protocol, replace import prefixes.
    if package_path.parents[1].name == "aea":
        log("Replace import prefixes (it's a library protocol)")
        replace_in_directory(package_path.name)

    package_readme_file = package_path / README_FILENAME
    if package_readme_file.exists():
        log(f"Copy the README {package_readme_file} into the new generated protocol.")
        shutil.copyfile(
            package_readme_file, Path("protocols", package_path.name, README_FILENAME)
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
    shutil.copytree(Path("protocols", package_path.name), package_path)


def _fingerprint_protocol(name: str):
    """Fingerprint the generated (and modified) protocol."""
    log(f"Fingerprint the generated (and modified) protocol '{name}'")
    protocol_config = load_component_configuration(
        ComponentType.PROTOCOL, Path("protocols", name), skip_consistency_check=True
    )
    run_aea("fingerprint", "protocol", str(protocol_config.public_id))


def _process_protocol(package_path: Path) -> None:
    """
    Process a protocol package.

    It means:
    - extract protocol specification from the README
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
    _fingerprint_protocol(package_path.name)
    _update_original_protocol(package_path)


def _check_preliminaries():
    """Check that the required software is in place."""
    try:
        import aea  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
    except ModuleNotFoundError:
        enforce(False, "'aea' package not installed.")
    enforce(shutil.which("black") is not None, "black command line tool not found.")
    enforce(shutil.which("isort") is not None, "isort command line tool not found.")


def main():
    """Run the script."""
    _check_preliminaries()
    with AEAProject():

        for package_path in PROTOCOL_PATHS:
            log("=" * 100)
            log(f"Processing protocol at path {package_path}")
            _process_protocol(package_path)


if __name__ == "__main__":
    main()
