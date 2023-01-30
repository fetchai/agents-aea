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

"""Test dialogues module for t_protocol_no_ct protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from tests.data.packages.fetchai.protocols.t_protocol_no_ct.dialogues import (
    TProtocolNoCtDialogue,
    TProtocolNoCtDialogues,
)
from tests.data.packages.fetchai.protocols.t_protocol_no_ct.message import (
    TProtocolNoCtMessage,
)


class TestDialoguesTProtocolNoCt(BaseProtocolDialoguesTestCase):
    """Test for the 't_protocol_no_ct' protocol dialogues."""

    MESSAGE_CLASS = TProtocolNoCtMessage

    DIALOGUE_CLASS = TProtocolNoCtDialogue

    DIALOGUES_CLASS = TProtocolNoCtDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = TProtocolNoCtDialogue.Role.ROLE_1  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some_bytes",
            content_int=12,
            content_float=1.0,
            content_bool=True,
            content_str="some str",
        )
