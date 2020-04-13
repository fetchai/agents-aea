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


def write_envelope_to_file(envelope: Envelope, file_path: str) -> None:
    """
    Write an envelope to input_file.
    Run from agent's directory.

    :param envelope: Envelope.
    :param file_path: the file path

    :return: None
    """
    encoded_envelope_str = "{},{},{},{},".format(
        envelope.to,
        envelope.sender,
        envelope.protocol_id,
        envelope.message.decode("utf-8"),
    )
    encoded_envelope = encoded_envelope_str.encode("utf-8")
    with open(Path(file_path), "ab+") as f:
        f.write(encoded_envelope)
        f.flush()


def read_envelope_from_file(file_path: str):
    """
    Readlines the output_file.
    Run from agent's directory.

    :param file_path the file path.

    :return: envelope
    """
    lines = []
    with open(Path(file_path), "rb+") as f:
        lines.extend(f.readlines())

    assert len(lines) == 2
    line = lines[0] + lines[1]
    to_b, sender_b, protocol_id_b, message, end = line.strip().split(b",", maxsplit=4)
    to = to_b.decode("utf-8")
    sender = sender_b.decode("utf-8")
    protocol_id = PublicId.from_str(protocol_id_b.decode("utf-8"))
    assert end in [b"", b"\n"]

    return Envelope(to=to, sender=sender, protocol_id=protocol_id, message=message,)
