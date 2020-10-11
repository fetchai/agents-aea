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
"""This module contains generic tools for AEA end-to-end testing."""

from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

from aea.cli.utils.config import handle_dotted_path
from aea.configurations.base import (
    PackageConfiguration,
    PackageType,
    PublicId,
    SkillConfig,
)
from aea.connections.stub.connection import write_envelope
from aea.exceptions import enforce
from aea.helpers.base import yaml_dump, yaml_dump_all
from aea.mail.base import Envelope
from aea.test_tools.constants import DEFAULT_AUTHOR


def write_envelope_to_file(envelope: Envelope, file_path: str) -> None:
    """
    Write an envelope to a file.

    :param envelope: Envelope.
    :param file_path: the file path

    :return: None
    """
    with open(Path(file_path), "ab+") as f:
        write_envelope(envelope, f)


def read_envelope_from_file(file_path: str):
    """
    Read an envelope from a file.

    :param file_path the file path.

    :return: envelope
    """
    lines = []
    with open(Path(file_path), "rb+") as f:
        lines.extend(f.readlines())

    enforce(len(lines) == 2, "Did not find two lines.")
    line = lines[0] + lines[1]
    to_b, sender_b, protocol_id_b, message, end = line.strip().split(b",", maxsplit=4)
    to = to_b.decode("utf-8")
    sender = sender_b.decode("utf-8")
    protocol_id = PublicId.from_str(protocol_id_b.decode("utf-8"))
    enforce(end in [b"", b"\n"], "Envelope improperly formatted.")

    return Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message,)


def _nested_set(
    configuration_obj: PackageConfiguration, keys: List, value: Any
) -> None:
    """
    Nested set a value to a dict. Force sets the value, overwriting any present values.

    :param configuration_obj: configuration object
    :param keys: list of keys.
    :param value: a value to set.

    :return: None.
    """
    dic = {}  # type: Dict[str, Any]
    root_key = keys[0]
    if (
        type(configuration_obj) == SkillConfig
        and root_key in SkillConfig.FIELDS_WITH_NESTED_FIELDS
    ):
        root_attr = getattr(configuration_obj, root_key)
        skill_component_id = keys[1]
        skill_component_config = root_attr.read(skill_component_id)
        for key in keys[3:-1]:
            dic = dic.setdefault(key, OrderedDict())
        dic[keys[-1]] = value if type(value) != dict else OrderedDict(value)
        skill_component_config.args.update(dic)
        root_attr.update(skill_component_id, skill_component_config)
    else:
        for key in keys[:-1]:
            dic = dic.setdefault(key, OrderedDict())
        dic[keys[-1]] = value if type(value) != dict else OrderedDict(value)
        setattr(configuration_obj, root_key, dic[root_key])


def force_set_config(
    dotted_path: str, value: Any, author: str = DEFAULT_AUTHOR
) -> None:
    """
    Set an AEA config without validation.

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

    :return: None.
    """
    settings_keys, config_file_path, config_loader, _ = handle_dotted_path(
        dotted_path, author
    )

    with config_file_path.open() as fp:
        config = config_loader.load(fp)

    _nested_set(config, settings_keys, value)

    if config.package_type == PackageType.AGENT:
        json_data = config.ordered_json
        component_configurations = json_data.pop("component_configurations")
        yaml_dump_all(
            [json_data] + component_configurations, config_file_path.open("w")
        )
    else:
        yaml_dump(config.ordered_json, config_file_path.open("w"))
