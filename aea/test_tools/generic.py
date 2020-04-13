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

from aea.configurations.base import PublicId
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.test_tools.config import DEFAULT_INPUT_FILE_NAME, DEFAULT_OUTPUT_FILE_NAME


def create_default_message(
    content, dialogue_reference=("", ""), message_id=1, target=0,
):
    """
    Create a default message.

    :param content: bytes str message content.

    :return: DefaultMessage
    """
    return DefaultMessage(
        dialogue_reference=dialogue_reference,
        message_id=message_id,
        target=target,
        performative=DefaultMessage.Performative.BYTES,
        content=content,
    )


def create_envelope(
    agent_name, message, sender="sender", protocol_id=DefaultMessage.protocol_id,
):
    """
    Create an envelope.

    :param agent_name: str agent name.
    :param message: str or DefaultMessage object message.

    :return: Envelope
    """
    if type(message) == DefaultMessage:
        message = DefaultSerializer().encode(message)

    return Envelope(
        to=agent_name, sender=sender, protocol_id=protocol_id, message=message
    )


def encode_envelope(envelope: Envelope) -> bytes:
    """
    Encode an envelope.

    :param envelope: Envelope.

    :return: str encoded envelope.
    """
    encoded_envelope = "{},{},{},{},".format(
        envelope.to,
        envelope.sender,
        envelope.protocol_id,
        envelope.message.decode("utf-8"),
    )
    return encoded_envelope.encode("utf-8")


def write_envelope_to_file(envelope: Envelope) -> None:
    """
    Write an envelope to input_file.
    Run from agent's directory.

    :param envelope: Envelope.

    :return: None
    """
    encoded_envelope = encode_envelope(envelope)
    with open(Path(DEFAULT_INPUT_FILE_NAME), "ab+") as f:
        f.write(encoded_envelope)
        f.flush()


def read_envelope_from_file():
    """
    Readlines the output_file.
    Run from agent's directory.

    :return: list lines content of output_file.
    """
    lines = []
    with open(Path(DEFAULT_OUTPUT_FILE_NAME), "rb+") as f:
        lines.extend(f.readlines())

    assert len(lines) == 2
    line = lines[0] + lines[1]
    to, sender, protocol_id, message, end = line.strip().split(b",", maxsplit=4)
    to = to.decode("utf-8")
    sender = sender.decode("utf-8")
    protocol_id = PublicId.from_str(protocol_id.decode("utf-8"))
    assert end in [b"", b"\n"]

    return create_envelope(
        agent_name=to, message=message, sender=sender, protocol_id=protocol_id
    )
