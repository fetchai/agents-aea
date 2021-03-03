# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Module with generic utils of the aea cli."""
import os
from typing import Dict

import yaml
from click import ClickException

from aea.helpers.io import open_file


def load_yaml(filepath: str) -> Dict:
    """
    Read content from yaml file.

    :param filepath: str path to yaml file.

    :return: dict YAML content
    """
    with open_file(filepath, "r") as f:
        try:
            result = yaml.safe_load(f)
            return result if result is not None else {}
        except yaml.YAMLError as e:
            raise ClickException(
                "Loading yaml config from {} failed: {}".format(filepath, e)
            )


def is_readme_present(readme_path: str) -> bool:
    """
    Check is readme file present.

    This method is needed for proper testing.

    :param readme_path: path to readme file.

    :return: bool is readme file present.
    """
    return os.path.exists(readme_path)
