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

"""Common utils for scripts."""
import logging
import re
import subprocess  # nosec
import sys
from io import StringIO
from pathlib import Path
from typing import Match, cast

from aea.configurations.base import ProtocolSpecification
from aea.configurations.loader import ConfigLoader


SPECIFICATION_REGEX = re.compile(r"(---\nname.*\.\.\.)", re.DOTALL)
PROTOCOL_SPECIFICATION_ID_IN_SPECIFICATION_REGEX = re.compile(
    "^protocol_specification_id: (.*)$", re.MULTILINE
)
PACKAGES_DIR = Path("packages")


def setup_logger(name: str) -> logging.Logger:
    """Set up the logger."""
    FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger_ = logging.getLogger(name)
    logger_.setLevel(logging.INFO)
    return logger_


logger = setup_logger(__name__)


def enforce(condition: bool, message: str = "") -> None:
    """Custom assertion."""
    if not condition:
        raise AssertionError(message)


def check_working_tree_is_dirty() -> None:
    """Check if the current Git working tree is dirty."""
    print("Checking whether the Git working tree is dirty...")
    result = subprocess.check_output(["git", "diff", "--stat"])  # nosec
    if len(result) > 0:
        print("Git working tree is dirty:")
        print(result.decode("utf-8"))
        sys.exit(1)
    else:
        print("All good!")


def load_protocol_specification_from_string(
    specification_content: str,
) -> ProtocolSpecification:
    """Load a protocol specification from string."""
    file = StringIO(initial_value=specification_content)
    config_loader = ConfigLoader(
        "protocol-specification_schema.json", ProtocolSpecification
    )
    protocol_spec = config_loader.load_protocol_specification(file)
    return protocol_spec


def get_protocol_specification_from_readme(package_path: Path) -> str:
    """Get the protocol specification from the package README."""
    logger.info(f"Get protocol specification from README {package_path}")
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
