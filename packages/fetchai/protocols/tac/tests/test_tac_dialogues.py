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

"""Test dialogues module for tac protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.fetchai.protocols.tac.dialogues import TacDialogue, TacDialogues
from packages.fetchai.protocols.tac.message import TacMessage


class TestDialoguesTac(BaseProtocolDialoguesTestCase):
    """Test for the 'tac' protocol dialogues."""

    MESSAGE_CLASS = TacMessage

    DIALOGUE_CLASS = TacDialogue

    DIALOGUES_CLASS = TacDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = TacDialogue.Role.CONTROLLER  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=TacMessage.Performative.REGISTER,
            agent_name="some str",
        )
