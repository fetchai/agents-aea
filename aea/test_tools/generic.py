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

from pathlib import Path
from typing import Any, Dict, List

import yaml

from aea.cli.utils.config import handle_dotted_path
from aea.configurations.base import PublicId
from aea.mail.base import Envelope


def write_envelope_to_file(envelope: Envelope, file_path: str) -> None:
    """
    Write an envelope to a file.

    :param envelope: Envelope.
    :param file_path: the file path

    :return: None
    """
    encoded_envelope_str = "{},{},{},{},".format(
        envelope.to,
        envelope.sender,
        envelope.protocol_id,
        envelope.message_bytes.decode("utf-8"),
    )
    encoded_envelope = encoded_envelope_str.encode("utf-8")
    with open(Path(file_path), "ab+") as f:
        f.write(encoded_envelope)
        f.flush()


def read_envelope_from_file(file_path: str):
    """
    Read an envelope from a file.

    :param file_path the file path.

    :return: envelope
    """
    lines = []
    with open(Path(file_path), "rb+") as f:
        lines.extend(f.readlines())

    assert len(lines) == 2, "Did not find two lines."
    line = lines[0] + lines[1]
    to_b, sender_b, protocol_id_b, message, end = line.strip().split(b",", maxsplit=4)
    to = to_b.decode("utf-8")
    sender = sender_b.decode("utf-8")
    protocol_id = PublicId.from_str(protocol_id_b.decode("utf-8"))
    assert end in [b"", b"\n"]

    return Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message,)


def _nested_set(dic: Dict, keys: List, value: Any) -> None:
    """
    Nested set a value to a dict.

    :param dic: target dict
    :param keys: list of keys.
    :param value: a value to set.

    :return: None.
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def force_set_config(dotted_path: str, value: Any) -> None:
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

    :return: None.
    """
    settings_keys, file_path, _ = handle_dotted_path(dotted_path)

    settings = {}
    with open(file_path, "r") as f:
        settings = yaml.safe_load(f)

    _nested_set(settings, settings_keys, value)

    with open(file_path, "w") as f:
        yaml.dump(settings, f, default_flow_style=False)
