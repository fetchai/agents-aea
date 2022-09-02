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
"""This module contains generic tools for AEA end-to-end testing."""

from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, cast

from aea.configurations.base import (
    CRUDCollection,
    ComponentConfiguration,
    PackageConfiguration,
    PackageType,
    PublicId,
    SkillConfig,
    dependencies_from_json,
)
from aea.configurations.manager import handle_dotted_path
from aea.exceptions import enforce
from aea.helpers.file_io import write_envelope
from aea.helpers.io import open_file
from aea.helpers.yaml_utils import yaml_dump, yaml_dump_all
from aea.mail.base import Envelope
from aea.test_tools.constants import DEFAULT_AUTHOR


def write_envelope_to_file(envelope: Envelope, file_path: str) -> None:
    """
    Write an envelope to a file.

    :param envelope: Envelope.
    :param file_path: the file path
    """
    with open(Path(file_path), "ab+") as f:
        write_envelope(envelope, f)


def read_envelope_from_file(file_path: str) -> Envelope:
    """
    Read an envelope from a file.

    :param file_path: the file path.

    :return: envelope
    """
    lines = []
    with open(Path(file_path), "rb+") as f:
        lines.extend(f.readlines())

    enforce(len(lines) == 2, "Did not find two lines.")
    line = lines[0] + lines[1]
    to_b, sender_b, protocol_specification_id_b, message, end = line.strip().split(
        b",", maxsplit=4
    )
    to = to_b.decode("utf-8")
    sender = sender_b.decode("utf-8")
    protocol_specification_id = PublicId.from_str(
        protocol_specification_id_b.decode("utf-8")
    )
    enforce(end in [b"", b"\n"], "Envelope improperly formatted.")

    return Envelope(
        to=to,
        sender=sender,
        protocol_specification_id=protocol_specification_id,
        message=message,
    )


def _nested_set(
    configuration_obj: PackageConfiguration, keys: List, value: Any
) -> None:
    """
    Nested set a value to a dict. Force sets the values, overwriting any present values, but maintaining schema validation.

    :param configuration_obj: configuration object
    :param keys: list of keys.
    :param value: a value to set.
    """

    def get_nested_ordered_dict_from_dict(input_dict: Dict) -> Dict:
        _dic = {}
        for _key, _value in input_dict.items():
            if isinstance(_value, dict):
                _dic[_key] = OrderedDict(get_nested_ordered_dict_from_dict(_value))
            else:
                _dic[_key] = _value
        return _dic

    def get_nested_ordered_dict_from_keys_and_value(
        keys: List[str], value: Any
    ) -> Dict:
        _dic = (
            OrderedDict(get_nested_ordered_dict_from_dict(value))
            if isinstance(value, dict)
            else value
        )
        for key in keys[::-1]:
            _dic = OrderedDict({key: _dic})
        return _dic

    root_key = keys[0]
    if (
        isinstance(configuration_obj, SkillConfig)
        and root_key in SkillConfig.FIELDS_WITH_NESTED_FIELDS
    ):
        root_attr = getattr(configuration_obj, root_key)
        length = len(keys)
        if length < 3 or keys[2] not in SkillConfig.NESTED_FIELDS_ALLOWED_TO_UPDATE:
            raise ValueError(f"Invalid keys={keys}.")  # pragma: nocover
        skill_component_id = keys[1]
        skill_component_config = root_attr.read(skill_component_id)
        if length == 3 and isinstance(value, dict):  # root.skill_component_id.args
            # set all args
            skill_component_config.args = get_nested_ordered_dict_from_dict(value)
        elif len(keys) >= 4:  # root.skill_component_id.args.[keys]
            # update some args
            dic = get_nested_ordered_dict_from_keys_and_value(keys[3:], value)
            skill_component_config.args.update(dic)
        else:
            raise ValueError(  # pragma: nocover
                f"Invalid keys={keys} and values={value}."
            )
        root_attr.update(skill_component_id, skill_component_config)
    else:
        root_attr = getattr(configuration_obj, root_key)
        if isinstance(root_attr, CRUDCollection):
            if isinstance(value, dict) and len(keys) == 1:  # root.
                for _key, _value in value.items():
                    dic = get_nested_ordered_dict_from_keys_and_value([_key], _value)
                    root_attr.update(_key, dic[_key])
            elif len(keys) >= 2:  # root.[keys]
                dic = get_nested_ordered_dict_from_keys_and_value(keys[1:], value)
                root_attr.update(keys[1], dic[keys[1]])
            else:
                raise ValueError(  # pragma: nocover
                    f"Invalid keys={keys} and values={value}."
                )
        elif root_key == "dependencies":
            enforce(
                isinstance(configuration_obj, ComponentConfiguration),
                "Cannot only set dependencies to ComponentConfiguration instances.",
            )
            configuration_obj = cast(ComponentConfiguration, configuration_obj)
            new_pypi_dependencies = dependencies_from_json(value)
            configuration_obj.pypi_dependencies = new_pypi_dependencies
        else:
            dic = get_nested_ordered_dict_from_keys_and_value(keys, value)
            setattr(configuration_obj, root_key, dic[root_key])


def nested_set_config(
    dotted_path: str, value: Any, author: str = DEFAULT_AUTHOR
) -> None:
    """
    Set an AEA config with nested values.

    Run from agent's directory.

    Allowed dotted_path:
        'agent.an_attribute_name'
        'protocols.my_protocol.an_attribute_name'
        'connections.my_connection.an_attribute_name'
        'contracts.my_contract.an_attribute_name'
        'skills.my_skill.an_attribute_name'
        'vendor.author.[protocols|connections|skills].package_name.attribute_name

    :param dotted_path: dotted path to a setting.
    :param value: a value to assign. Must be of yaml serializable type.
    :param author: the author name, used to parse the dotted path.
    """
    settings_keys, config_file_path, config_loader, _ = handle_dotted_path(
        dotted_path, author
    )
    with open_file(config_file_path) as fp:
        config = config_loader.load(fp)

    _nested_set(config, settings_keys, value)

    if config.package_type == PackageType.AGENT:
        json_data = config.ordered_json
        component_configurations = json_data.pop("component_configurations")
        with open_file(config_file_path, "w") as fp:
            yaml_dump_all([json_data] + component_configurations, fp)
    else:
        with open_file(config_file_path, "w") as fp:
            yaml_dump(config.ordered_json, fp)
