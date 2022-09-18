# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import os
import pprint
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
from pathlib import Path
from typing import Any, List, Tuple, cast

import click
import semver

from aea.cli.registry.utils import download_file, extract, request_api
from aea.common import JSONLike
from aea.configurations.base import ComponentType, ProtocolConfig
from aea.configurations.constants import (
    AEA_TEST_DIRNAME,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_README_FILE,
    PROTOCOLS,
)
from aea.configurations.data_types import PackageId, PublicId
from aea.configurations.loader import ConfigLoaders, load_component_configuration
from aea.exceptions import enforce
from aea.helpers.git import check_working_tree_is_dirty
from aea.helpers.protocols import get_protocol_specification_from_readme
from aea.manager.helpers import AEAProject


SPECIFICATION_REGEX = re.compile(r"(---\nname.*\.\.\.)", re.DOTALL)
LIBPROTOC_VERSION = "libprotoc 3.19.4"
CUSTOM_TYPE_MODULE_NAME = "custom_types.py"
PROTOCOL_GENERATOR_DOCSTRING_REGEX = "It was created with protocol buffer compiler version `libprotoc .*` and aea protocol generator version `.*`."

logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s")
logger = logging.getLogger("generate_all_protocols")
logger.setLevel(logging.INFO)


def find_protocols_in_local_registry(packages_dir: Path) -> List[Path]:
    """Find all protocols in local registry."""
    return [
        p.parent.absolute()
        for p in packages_dir.glob(f"**/{DEFAULT_PROTOCOL_CONFIG_FILE}")
    ]


def log(message: str, level: int = logging.INFO) -> None:
    """Produce a logging message."""
    logger.log(level, message)


def log_separator(length: int = 100) -> None:
    """Log separator."""
    click.echo("=" * length)


def _save_specification_in_temporary_file(
    name: str, specification_content: str
) -> None:
    """
    Save the specification in a temporary file.

    :param name: the name of the package.
    :param specification_content: the specification content.
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
    """
    cmd = ["generate", "protocol", os.path.join("..", package_path.name) + ".yaml"]
    log(f"Generate the protocol. Command: {pprint.pformat(cmd)}")
    AEAProject.run_aea(*cmd)


def run_isort_and_black(directory: Path, **kwargs: Any) -> None:
    """Run black and isort against a directory."""
    kwargs["stdout"] = subprocess.PIPE

    try:
        # check if black and isort is installed
        import black  # type: ignore  # noqa  # pylint: disable=unused-import,import-outside-toplevel
        import isort  # type: ignore  # noqa  # pylint: disable=unused-import,import-outside-toplevel
    except ImportError as e:
        raise click.ClickException(str(e)) from e

    AEAProject.run_cli(
        sys.executable,
        "-m",
        "black",
        "-q",
        str(directory.absolute()),
        **kwargs,
    )
    AEAProject.run_cli(
        sys.executable,
        "-m",
        "isort",
        "--settings-path",
        "setup.cfg",
        str(directory.absolute()),
        **kwargs,
    )


def _fix_generated_protocol(package_path: Path) -> None:
    """
    Fix the generated protocol.

    That means:
    - replacing the prefix of import statements for default protocols;
    - restore the original custom types, if any.
    - copy the README, if any.

    :param package_path: path to the protocol package. Used also to recover the protocol name.
    """
    custom_types_module = package_path / CUSTOM_TYPE_MODULE_NAME
    if custom_types_module.exists():
        log(f"Restore original custom types in {package_path}")
        file_to_replace = Path(PROTOCOLS, package_path.name, CUSTOM_TYPE_MODULE_NAME)
        file_to_replace.write_text(custom_types_module.read_text())

    package_readme_file = package_path / DEFAULT_README_FILE
    if package_readme_file.exists():
        log(f"Copy the README {package_readme_file} into the new generated protocol.")
        shutil.copyfile(
            package_readme_file,
            Path(PROTOCOLS, package_path.name, DEFAULT_README_FILE),
        )

    tests_module = package_path / AEA_TEST_DIRNAME
    if tests_module.is_dir():
        log(f"Restore original `tests` directory in {package_path}")
        shutil.copytree(
            tests_module, Path(PROTOCOLS, package_path.name, AEA_TEST_DIRNAME)
        )


def _update_original_protocol(package_path: Path) -> None:
    """
    Update the original protocol.

    :param package_path: the path to the original package. Used to recover the protocol name.
    """
    log(f"Copy the new protocol into the original directory {package_path}")
    shutil.rmtree(package_path)
    shutil.copytree(Path(PROTOCOLS, package_path.name), package_path)


def _fingerprint_protocol(name: str) -> None:
    """Fingerprint the generated (and modified) protocol."""
    log(f"Fingerprint the generated (and modified) protocol '{name}'")
    protocol_config = load_component_configuration(
        ComponentType.PROTOCOL,
        Path(PROTOCOLS, name),
        skip_consistency_check=True,
    )
    AEAProject.run_aea("fingerprint", "protocol", str(protocol_config.public_id))


def _parse_generator_docstring(package_path: Path) -> str:
    """
    Parse protocol generator docstring.

    The docstring this function searches is in the __init__.py module
    and it is of the form:

        It was created with protocol buffer compiler version `libprotoc ...` and aea version `...`.


    :param package_path: path to the protocol package
    :return: the docstring
    """
    content = (package_path / "__init__.py").read_text()
    regex = re.compile(PROTOCOL_GENERATOR_DOCSTRING_REGEX)
    match = regex.search(content)
    if match is None:
        raise ValueError("protocol generator docstring not found")
    return match.group(0)


def _replace_generator_docstring(package_path: Path, replacement: str) -> None:
    """
    Replace the generator docstring in the __init__.py module.

    (see _parse_generator_docstring for more details).

    :param package_path: path to the
    :param replacement: the replacement to use.
    """
    protocol_name = package_path.name
    init_module = Path(PROTOCOLS) / protocol_name / "__init__.py"
    content = init_module.read_text()
    content = re.sub(PROTOCOL_GENERATOR_DOCSTRING_REGEX, replacement, content)
    init_module.write_text(content)


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
    """
    # extract protocol specification file from README
    current_specification_content = get_protocol_specification_from_readme(package_path)

    # download latest protocol id and extract its protocol specification as above
    configuration: ProtocolConfig = cast(
        ProtocolConfig,
        load_component_configuration(ComponentType.PROTOCOL, package_path),
    )
    temp_directory = Path(tempfile.mkdtemp())
    try:
        download_package(configuration.package_id, str(temp_directory))
    except click.ClickException:
        log("Protocol specification id not bumped - new protocol.")
        return
    downloaded_package_directory = temp_directory / configuration.name
    old_specification_content = get_protocol_specification_from_readme(
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


def replace_in_directory(name: str, replacement_pairs: List[Tuple[str, str]]) -> None:
    """
    Replace text in directory.

    :param name: the protocol name.
    :param replacement_pairs: a list of pairs of strings (to_replace, replacement).
    """
    log(f"Replace prefix of import statements in directory '{name}'")
    package_dir = Path(PROTOCOLS, name)
    for submodule in package_dir.rglob("*.py"):
        log(f"Process submodule {submodule.relative_to(package_dir)}")
        for to_replace, replacement in replacement_pairs:
            if to_replace not in submodule.read_text():
                continue
            submodule.write_text(submodule.read_text().replace(to_replace, replacement))


def _process_packages_protocol(
    package_path: Path,
    preserve_generator_docstring: bool,
    no_format: bool,
    root_dir: Path,
) -> None:
    """
    Process protocol package from local registry.

    If the flag '--no-bump' is specified, it means the protocol generator
    string that records the AEA and the protoc version used, i.e.:

        It was created with protocol buffer compiler version `libprotoc ...` and aea version `...`.

    must not be updated, as the 'AEA' version could have been changed.

    It means:
    - extract protocol specification from README
    - generate the protocol in the current AEA project
    - fix the generated protocol (e.g. import prefixed, custom types, ...)
    - update the original protocol with the newly generated one.

    It assumes the working directory is an AEA project.

    :param package_path: path to the package.
    :param preserve_generator_docstring: if True, the protocol generator docstring is preserved (see above).
    :param no_format: If True, won't run the formatters
    :param root_dir: Path to open-aea repository
    """
    if preserve_generator_docstring:
        # save the old protocol generator docstring
        old_protocol_generator_docstring = _parse_generator_docstring(package_path)
    specification_content = get_protocol_specification_from_readme(package_path)
    _save_specification_in_temporary_file(package_path.name, specification_content)
    _generate_protocol(package_path)
    _fix_generated_protocol(package_path)

    packages_dir_parent = package_path.parent.parent.parent.parent
    if root_dir != packages_dir_parent:
        if root_dir not in packages_dir_parent.parents:
            raise ValueError(
                "Packages dir should be a sub directory of the root directory."
            )

        relative_import_path = ".".join(
            packages_dir_parent.parts[len(root_dir.parts) :]
        )
        replacements = [
            (
                f"from packages.fetchai.protocols.{package_path.name}",
                f"from {relative_import_path}.packages.fetchai.protocols.{package_path.name}",
            )
        ]
        replace_in_directory(package_path.name, replacements)

    if preserve_generator_docstring:
        _replace_generator_docstring(package_path, old_protocol_generator_docstring)

    if not no_format:
        run_isort_and_black(Path(PROTOCOLS, package_path.name), cwd=str(root_dir))

    _fingerprint_protocol(package_path.name)
    _update_original_protocol(package_path)


@click.command(name="generate-all-protocols")
@click.argument(
    "packages_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    default=Path("packages/"),
)
@click.option(
    "--no-bump",
    is_flag=True,
    default=False,
    help="no_bump implies to ignore the docstring",
)
@click.option(
    "--no-format",
    is_flag=True,
    default=False,
    help="If set to True, formatters won't run.",
)
@click.option(
    "--root-dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Path to root dir.",
    default=Path(".").resolve(),
)
@click.option(
    "--check-clean",
    is_flag=True,
    help="Check if git tree is clean..",
)
def generate_all_protocols(
    packages_dir: Path,
    no_bump: bool,
    no_format: bool,
    root_dir: Path,
    check_clean: bool,
) -> None:
    """Generate all protocols."""

    _check_preliminaries()

    packages_dir = Path(packages_dir).absolute()
    root_dir = Path(root_dir).absolute()
    all_protocols = find_protocols_in_local_registry(packages_dir)

    with AEAProject():
        for package_path in all_protocols:
            log_separator()
            log(f"Processing protocol at path {package_path}")
            if not no_bump:
                _bump_protocol_specification_id_if_needed(package_path)
            _process_packages_protocol(
                package_path,
                no_bump,
                no_format,
                root_dir,
            )

    if check_clean:
        is_clean = check_working_tree_is_dirty()
        if not is_clean:
            print(
                "You should bump PROTOCOL_GENERATOR_VERSION in aea/protocols/__init__.py "
                "and rerun the protocol generation"
            )
            sys.exit(1)
