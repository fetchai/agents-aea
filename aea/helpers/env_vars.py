# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Implementation of the environment variables support."""
import json
import re
from collections.abc import Mapping as MappingType
from typing import Any, Dict, List, Mapping, Union

from aea.helpers.constants import (
    FALSE_EQUIVALENTS,
    FROM_STRING_TO_TYPE,
    JSON_TYPES,
    NULL_EQUIVALENTS,
)


ENV_VARIABLE_RE = re.compile(
    r"^\$\{(?P<name>\w+)(:(?P<type>\w+)(:(?P<default>.+))?)?\}$", re.I
)


def is_env_variable(value: Any) -> bool:
    """Check is variable string with env variable pattern."""
    return isinstance(value, str) and bool(ENV_VARIABLE_RE.match(value))


NotSet = object()


def replace_with_env_var(
    value: str, env_variables: dict, default_value: Any = NotSet
) -> JSON_TYPES:
    """Replace env var with value."""
    result = ENV_VARIABLE_RE.match(value)

    if not result:
        return value

    var_name = result.groupdict()["name"]
    type_str = result.groupdict()["type"]
    default = result.groupdict()["default"]

    if var_name in env_variables:
        var_value = env_variables[var_name]
    elif default is not None:
        var_value = default
    elif default_value is not NotSet:
        var_value = default_value
    else:
        raise ValueError(
            f"`{var_name}` not found in env variables and no default value set! Please ensure a .env file is provided."
        )

    if type_str is not None:
        var_value = convert_value_str_to_type(var_value, type_str)

    return var_value


def apply_env_variables(
    data: Union[Dict, List[Dict]],
    env_variables: Mapping[str, Any],
    default_value: Any = NotSet,
) -> JSON_TYPES:
    """Create new resulting dict with env variables applied."""

    if isinstance(data, (list, tuple)):
        result = []
        for i in data:
            result.append(apply_env_variables(i, env_variables, default_value))
        return result

    if isinstance(data, MappingType):
        return {
            apply_env_variables(k, env_variables, default_value): apply_env_variables(
                v, env_variables, default_value
            )
            for k, v in data.items()
        }
    if is_env_variable(data):
        return replace_with_env_var(data, env_variables, default_value)

    return data


def convert_value_str_to_type(value: str, type_str: str) -> JSON_TYPES:
    """Convert value by type name to native python type."""
    try:
        type_ = FROM_STRING_TO_TYPE[type_str]
        if type_ == bool:
            return value not in FALSE_EQUIVALENTS
        if type_ is None or value in NULL_EQUIVALENTS:
            return None
        if type_ in (dict, list):
            return json.loads(value)
        return type_(value)
    except (ValueError, json.decoder.JSONDecodeError):  # pragma: no cover
        raise ValueError(f"Cannot convert string `{value}` to type `{type_.__name__}`")  # type: ignore
