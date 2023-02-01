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

"""Test dialogues module for gym protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.fetchai.protocols.gym.dialogues import GymDialogue, GymDialogues
from packages.fetchai.protocols.gym.message import GymMessage


class TestDialoguesGym(BaseProtocolDialoguesTestCase):
    """Test for the 'gym' protocol dialogues."""

    MESSAGE_CLASS = GymMessage

    DIALOGUE_CLASS = GymDialogue

    DIALOGUES_CLASS = GymDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = GymDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=GymMessage.Performative.RESET,
        )
