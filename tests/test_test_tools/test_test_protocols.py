# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
"""This module contains a test for aea.test_tools.test_protocol."""


from typing import List, Type

from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import Dialogues
from aea.test_tools.test_protocol import (
    BaseProtocolDialoguesTestCase,
    BaseProtocolMessagesTestCase,
)

from tests.data.packages.fetchai.protocols.t_protocol.dialogues import (
    TProtocolDialogue,
    TProtocolDialogues,
)
from tests.data.packages.fetchai.protocols.t_protocol.message import (
    CustomDataModel,
    TProtocolMessage,
)


custom_data_model = CustomDataModel(
    bool_field=True,
    bytes_field=b"",
    dict_field={},
    float_field=1.1,
    set_field=set(),
    str_field="",
    list_field=[],
    int_field=1,
)


class TestMessages(BaseProtocolMessagesTestCase):
    """Base class to test message construction for the protocol."""

    MESSAGE_CLASS = TProtocolMessage

    def build_messages(self) -> List[Message]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
                content_ct=custom_data_model,
            )
        ]

    def build_inconsistent(self) -> List[Message]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
            ),
        ]


class TestDialogues(BaseProtocolDialoguesTestCase):
    """Test dialogues."""

    MESSAGE_CLASS: Type[Message] = TProtocolMessage
    DIALOGUE_CLASS: Type[BaseDialogue] = TProtocolDialogue
    DIALOGUES_CLASS: Type[Dialogues] = TProtocolDialogues
    ROLE_FOR_THE_FIRST_MESSAGE = TProtocolDialogue.Role.ROLE_1

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
            content_ct=custom_data_model,
        )
