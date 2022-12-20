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
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, cast

from aea.configurations.data_types import PublicId
from aea.helpers.constants import (
    FALSE_EQUIVALENTS,
    FROM_STRING_TO_TYPE,
    JSON_TYPES,
    NULL_EQUIVALENTS,
)


ENV_VARIABLE_RE = re.compile(r"^\$\{(([A-Z0-9_]+):?)?([a-z]+)?(:(.+))?}$")


def is_env_variable(value: Any) -> bool:
    """Check is variable string with env variable pattern."""
    return isinstance(value, str) and bool(ENV_VARIABLE_RE.match(value))


def export_path_to_env_var_string(export_path: List[str]) -> str:
    """Conver export path to environment variable string."""
    env_var_string = "_".join(map(str, export_path))
    return env_var_string.upper()


NotSet = object()


def replace_with_env_var(
    value: str,
    env_variables: dict,
    default_value: Any = NotSet,
    default_var_name: Optional[str] = None,
) -> JSON_TYPES:
    """Replace env var with value."""
    result = ENV_VARIABLE_RE.match(value)

    if not result:
        return value

    _, var_name, type_str, _, default = result.groups()
    if var_name is None and default_var_name is not None:
        var_name = default_var_name

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
    path: Optional[List[str]] = None,
    default_value: Any = NotSet,
) -> JSON_TYPES:
    """Create new resulting dict with env variables applied."""
    path = path or []

    if isinstance(data, (list, tuple)):
        result = []
        for i, obj in enumerate(data):
            result.append(
                apply_env_variables(
                    data=obj,
                    env_variables=env_variables,
                    path=[*path, str(i)],
                    default_value=default_value,
                )
            )
        return result

    if isinstance(data, MappingType):
        return {
            k: apply_env_variables(
                data=v,
                env_variables=env_variables,
                path=[*path, k],
                default_value=default_value,
            )
            for k, v in data.items()
        }

    if is_env_variable(data):
        return replace_with_env_var(
            data,
            env_variables,
            default_value,
            default_var_name=export_path_to_env_var_string(export_path=path),
        )

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
    except (ValueError, json.decoder.JSONDecodeError):
        raise ValueError(f"Cannot convert string `{value}` to type `{type_.__name__}`")  # type: ignore
    except KeyError:
        raise KeyError(f"`{type_str}` is not a valid python data type")


def apply_env_variables_on_agent_config(
    data: List[Dict],
    env_variables: Mapping[str, Any],
) -> List[Dict]:
    """Create new resulting dict with env variables applied."""

    agent_config, *overrides = data
    agent_config_new = apply_env_variables(
        data=agent_config,
        env_variables=env_variables,
        path=[
            "agent",
        ],
    )

    overrides_new = []
    for component_config in overrides:
        component_name = PublicId.from_str(
            cast(str, component_config.get("public_id")),
        ).name
        component_type = cast(str, component_config.get("type"))
        new_component_config = cast(
            Dict,
            apply_env_variables(
                data=component_config,
                env_variables=env_variables,
                path=[
                    component_type,
                    component_name,
                ],
            ),
        )
        overrides_new.append(new_component_config)

    return [cast(Dict, agent_config_new), *overrides_new]


def is_strict_list(data: Union[List, Tuple]) -> bool:
    """
    Check if a data list is an strict list

    The data list contains a mapping object we need to process it as an
    object containing configurable parameters. For example

    cert_requests:
      - public_key: example_public_key

    This will get exported as `CONNECTION_NAME_CERT_REQUESTS_0_PUBLIC_KEY=example_public_key`

    Where as

    parameters:
     - hello
     - world

     will get exported as `SKILL_NAME_PARAMETERS=["hello", "world"]`

    :param data: Data list
    :return: Boolean specifying whether it's a strict list or not
    """
    is_strict = True
    for obj in data:
        if isinstance(obj, dict):
            return False
        if isinstance(obj, (list, tuple)):
            if not is_strict_list(data=obj):
                return False
    return is_strict


def generate_env_vars_recursively(
    data: Union[Dict, List],
    export_path: List[str],
) -> Dict:
    """Generate environment variables recursively."""
    env_var_dict = {}

    if isinstance(data, dict):
        for key, value in data.items():
            env_var_dict.update(
                generate_env_vars_recursively(
                    data=value,
                    export_path=[*export_path, key],
                )
            )
    elif isinstance(data, list):
        if is_strict_list(data=data):
            env_var_dict[
                export_path_to_env_var_string(export_path=export_path)
            ] = json.dumps(data)
        else:
            for key, value in enumerate(data):
                env_var_dict.update(
                    generate_env_vars_recursively(
                        data=value,
                        export_path=[*export_path, key],
                    )
                )
    else:
        env_var_dict[export_path_to_env_var_string(export_path=export_path)] = data

    return env_var_dict
