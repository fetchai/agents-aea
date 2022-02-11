# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""Module with formatting utils of the aea cli."""

from typing import Dict, List

from aea.configurations.base import AgentConfig
from aea.configurations.loader import ConfigLoader
from aea.exceptions import enforce
from aea.helpers.io import open_file


def format_items(items: List[Dict]) -> str:
    """Format list of items (protocols/connections) to a string for CLI output."""
    list_str = ""
    for item in items:
        list_str += (
            "{line}\n"
            "Public ID: {public_id}\n"
            "Name: {name}\n"
            "Description: {description}\n"
            "Author: {author}\n"
            "Version: {version}\n"
            "{line}\n".format(
                name=item["name"],
                public_id=item["public_id"],
                description=item["description"],
                author=item["author"],
                version=item["version"],
                line="-" * 30,
            )
        )
    return list_str


def retrieve_details(name: str, loader: ConfigLoader, config_filepath: str) -> Dict:
    """Return description of a protocol, skill, connection."""
    with open_file(str(config_filepath)) as fp:
        config = loader.load(fp)
    item_name = config.agent_name if isinstance(config, AgentConfig) else config.name
    enforce(item_name == name, "Item names do not match!")
    return {
        "public_id": str(config.public_id),
        "name": item_name,
        "author": config.author,
        "description": config.description,
        "version": config.version,
    }


def sort_items(items: List[Dict]) -> List[Dict]:
    """
    Sort a list of dict items associated with packages.

    :param items: list of dicts that represent items.

    :return: sorted list.
    """
    return sorted(items, key=lambda k: k["name"])
