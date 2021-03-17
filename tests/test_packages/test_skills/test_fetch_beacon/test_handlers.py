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
"""This module contains the tests of the handler classes of the simple_data_request skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea_ledger_ethereum import EthereumApi

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.ledger_api.custom_types import State
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.fetch_beacon.behaviours import FetchBeaconBehaviour
from packages.fetchai.skills.fetch_beacon.dialogues import LedgerApiDialogues
from packages.fetchai.skills.fetch_beacon.handlers import LedgerApiHandler

from tests.conftest import ROOT_DIR


def keccak256(input_: bytes) -> bytes:
    """Compute hash."""
    return bytes(bytearray.fromhex(EthereumApi.get_hash(input_)[2:]))


LEDGER_ID = "fetchai"


class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of fetch_beacon skill."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "fetch_beacon")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup(**kwargs)
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.logger = cls._skill.skill_context.logger
        cls.fetch_beacon_behaviour = cast(
            FetchBeaconBehaviour,
            cls._skill.skill_context.behaviours.fetch_beacon_behaviour,
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_STATE,
                {
                    "ledger_id": LEDGER_ID,
                    "callable": "blocks",
                    "args": ("latest",),
                    "kwargs": LedgerApiMessage.Kwargs({}),
                },
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_BALANCE,
                {"ledger_id": LEDGER_ID, "address": "some_eth_address"},
            ),
        )

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        assert self.ledger_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle__handle_unidentified_dialogue(self):
        """Test handling an unidentified dialogoue"""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_id=LEDGER_ID,
            callable="blocks",
            args=("latest",),
            kwargs=LedgerApiMessage.Kwargs({}),
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_state(self):
        """Test handling a state"""

        # setup
        test_state = {
            "block_id": {"hash": "00000000"},
            "block": {
                "header": {"height": "1", "entropy": {"group_signature": "SIGNATURE"}}
            },
        }
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[:1]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=LedgerApiMessage.Performative.STATE,
            ledger_id=LEDGER_ID,
            state=State(LEDGER_ID, test_state),
        )

        # handle message
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # check that data was correctly entered into shared state
        beacon_data = {
            "entropy": keccak256("SIGNATURE".encode("utf-8")),
            "block_hash": bytes.fromhex("00000000"),
            "block_height": 1,
        }
        assert self.ledger_api_handler.context.shared_state["observation"] == {
            "beacon": beacon_data
        }

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "Beacon info: " + str({"block_height": 1, "entropy": "SIGNATURE"}),
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_invalid(self):
        """Test handling an invalid performative"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[1:]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=LedgerApiMessage.Performative.BALANCE,
            ledger_id=LEDGER_ID,
            balance=0,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ledger_api message of performative={incoming_message.performative} in dialogue={dialogue}.",
        )

        self.assert_quantity_in_outbox(0)

    def test_teardown(self):
        """Test the teardown method of the ledger_api handler."""
        assert self.ledger_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
