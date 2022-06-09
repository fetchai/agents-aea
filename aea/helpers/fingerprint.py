# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Helper tools for fingerprinting packages."""

import re
from pathlib import Path
from typing import Collection, Dict, Optional, Tuple

from aea.configurations.base import (
    AgentConfig,
    PackageConfiguration,
    _compute_fingerprint,
)


def _replace_fingerprint_non_invasive(
    fingerprint_dict: Dict[str, str], text: str
) -> str:
    """
    Replace the fingerprint in a configuration file (not invasive).

    We need this function because libraries like `yaml` may modify the
    content of the .yaml file when loading/dumping. Instead,
    working with the content of the file gives us finer granularity.

    :param fingerprint_dict: the fingerprint dictionary.
    :param text: the content of a configuration file.
    :return: the updated content of the configuration file.
    """

    def to_row(x: Tuple[str, str]) -> str:
        return x[0] + ": " + x[1]

    if len(fingerprint_dict) == 0:
        replacement = "\nfingerprint: {}\n"
    else:
        replacement = "\nfingerprint:\n  {}\n".format(
            "\n  ".join(map(to_row, sorted(fingerprint_dict.items())))
        )

    return re.sub(r"\nfingerprint:\W*\n(?:\W+.*\n)*", replacement, text)


def compute_fingerprint(  # pylint: disable=unsubscriptable-object
    package_path: Path,
    fingerprint_ignore_patterns: Optional[Collection[str]],
) -> Dict[str, str]:
    """
    Compute the fingerprint of a package.

    :param package_path: path to the package.
    :param fingerprint_ignore_patterns: filename patterns whose matches will be ignored.
    :return: the fingerprint
    """
    fingerprint = _compute_fingerprint(
        package_path,
        ignore_patterns=fingerprint_ignore_patterns,
    )
    return fingerprint


def update_fingerprint(configuration: PackageConfiguration) -> None:
    """
    Update the fingerprint of a package.

    :param configuration: the configuration object.
    """

    if configuration.directory is None:
        raise ValueError("configuration.directory cannot be None.")

    fingerprint = compute_fingerprint(
        configuration.directory, configuration.fingerprint_ignore_patterns
    )
    config_filepath = (
        configuration.directory / configuration.default_configuration_filename
    )
    old_content = config_filepath.read_text()
    new_content = _replace_fingerprint_non_invasive(fingerprint, old_content)
    config_filepath.write_text(new_content)


def check_fingerprint(configuration: PackageConfiguration) -> bool:
    """
    Check the fingerprint of a package, given the loaded configuration file.

    :param configuration: the configuration object.
    :return: True if the fingerprint match, False otherwise.
    """
    # we don't process agent configurations
    if isinstance(configuration, AgentConfig):
        return True

    if configuration.directory is None:
        raise ValueError("configuration.directory cannot be None.")

    expected_fingerprint = compute_fingerprint(
        configuration.directory, configuration.fingerprint_ignore_patterns
    )
    actual_fingerprint = configuration.fingerprint
    result = expected_fingerprint == actual_fingerprint
    if not result:
        print(
            "Fingerprints do not match for {} in {}".format(
                configuration.name, configuration.directory
            )
        )
    return result
