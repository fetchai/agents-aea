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

"""Test dialogues module for t_protocol protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from tests.data.packages.fetchai.protocols.t_protocol.custom_types import DataModel
from tests.data.packages.fetchai.protocols.t_protocol.dialogues import (
    TProtocolDialogue,
    TProtocolDialogues,
)
from tests.data.packages.fetchai.protocols.t_protocol.message import TProtocolMessage


class TestDialoguesTProtocol(BaseProtocolDialoguesTestCase):
    """Test for the 't_protocol' protocol dialogues."""

    MESSAGE_CLASS = TProtocolMessage

    DIALOGUE_CLASS = TProtocolDialogue

    DIALOGUES_CLASS = TProtocolDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = TProtocolDialogue.Role.ROLE_1  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
            content_ct=DataModel(
                int_field=12,
                bool_field=True,
                bytes_field=b"",
                dict_field={},
                float_field=1.0,
                set_field=set(),
                str_field="str",
                list_field=["str"],
            ),
        )
