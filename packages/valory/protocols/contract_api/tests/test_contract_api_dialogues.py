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

"""Test dialogues module for contract_api protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.valory.protocols.contract_api.custom_types import Kwargs
from packages.valory.protocols.contract_api.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage


class TestDialoguesContractApi(BaseProtocolDialoguesTestCase):
    """Test for the 'contract_api' protocol dialogues."""

    MESSAGE_CLASS = ContractApiMessage

    DIALOGUE_CLASS = ContractApiDialogue

    DIALOGUES_CLASS = ContractApiDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = ContractApiDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id="some str",
            contract_id="some str",
            callable="some str",
            kwargs=Kwargs({"key_1": 1, "key_2": 2}),
        )
