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
from typing import Dict, List

from click import ClickException

import yaml


def get_parent_object(obj: Dict, dotted_path: List[str]):
    """
    Given a nested dictionary, return the object denoted by the dotted path (if any).

    In particular if dotted_path = [], it returns the same object.

    :param obj: the dictionary.
    :param dotted_path: the path to the object.
    :return: the target dictionary
    :raise ValueError: if the path is not valid.
    """
    index = 0
    current_object = obj
    while index < len(dotted_path):
        current_attribute_name = dotted_path[index]
        current_object = current_object.get(current_attribute_name, None)
        # if the dictionary does not have the key we want, fail.
        if current_object is None:
            raise ValueError("Cannot get attribute '{}'".format(current_attribute_name))
        index += 1
    # if we are not at the last step and the attribute value is not a dictionary, fail.
    if isinstance(current_object, dict):
        return current_object
    else:
        raise ValueError("The target object is not a dictionary.")


def load_yaml(filepath: str) -> Dict:
    """
    Read content from yaml file.

    :param filepath: str path to yaml file.

    :return: dict YAML content
    """
    with open(filepath, "r") as f:
        try:
            return yaml.safe_load(f)
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
