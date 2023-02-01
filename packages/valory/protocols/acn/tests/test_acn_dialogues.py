# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

"""Test dialogues module for acn protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.valory.protocols.acn.custom_types import AgentRecord
from packages.valory.protocols.acn.dialogues import AcnDialogue, AcnDialogues
from packages.valory.protocols.acn.message import AcnMessage


class TestDialoguesAcn(BaseProtocolDialoguesTestCase):
    """Test for the 'acn' protocol dialogues."""

    MESSAGE_CLASS = AcnMessage

    DIALOGUE_CLASS = AcnDialogue

    DIALOGUES_CLASS = AcnDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = AcnDialogue.Role.NODE  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=AcnMessage.Performative.REGISTER,
            record=AgentRecord(
                address="address",
                public_key="pbk",
                peer_public_key="peerpbk",
                signature="sign",
                service_id="acn",
                ledger_id="fetchai",
            ),
        )
