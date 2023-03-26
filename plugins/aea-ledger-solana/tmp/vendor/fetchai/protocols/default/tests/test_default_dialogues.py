# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 fetchai
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

"""Test dialogues module for default protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
)
from packages.fetchai.protocols.default.message import DefaultMessage


class TestDialoguesDefault(BaseProtocolDialoguesTestCase):
    """Test for the 'default' protocol dialogues."""

    MESSAGE_CLASS = DefaultMessage

    DIALOGUE_CLASS = DefaultDialogue

    DIALOGUES_CLASS = DefaultDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = DefaultDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_bytes",
        )
