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

"""Protocol helpers."""

import re
from pathlib import Path
from typing import Match, cast

from aea.configurations.loader import load_protocol_specification_from_string
from aea.exceptions import enforce
from aea.helpers.logging import setup_logger


SPECIFICATION_REGEX = re.compile(r"(---\nname.*\.\.\.)", re.DOTALL)
PROTOCOL_SPECIFICATION_ID_IN_SPECIFICATION_REGEX = re.compile(
    "^protocol_specification_id: (.*)$", re.MULTILINE
)

_logger = setup_logger(__name__)


def get_protocol_specification_from_readme(package_path: Path) -> str:
    """Get the protocol specification from the package README."""
    _logger.info(f"Get protocol specification from README {package_path}")
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
    load_protocol_specification_from_string(specification_content)
    return specification_content


def get_protocol_specification_id_from_specification(specification: str) -> str:
    """Get the protocol specification id from the protocol specification."""
    matches = PROTOCOL_SPECIFICATION_ID_IN_SPECIFICATION_REGEX.findall(specification)
    enforce(
        len(matches) == 1,
        f"Expected exactly one protocol specification id, found: {matches}",
    )
    spec_id = matches[0]
    return spec_id
