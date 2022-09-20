# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module contains the tests of the handler classes of the generic buyer skill."""
# pylint: skip-file

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.search.models import Description
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.behaviours import GenericTransactionBehaviour
from packages.fetchai.skills.generic_buyer.dialogues import (
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.generic_buyer.handlers import (
    GenericFipaHandler,
    GenericLedgerApiHandler,
    GenericOefSearchHandler,
    GenericSigningHandler,
    LEDGER_API_ADDRESS,
)
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy
from packages.open_aea.protocols.signing.message import SigningMessage


PACKAGE_ROOT = Path(__file__).parent.parent


class TestGenericFipaHandler(BaseSkillTestCase):
    """Test fipa handler of generic buyer."""

    path_to_skill = PACKAGE_ROOT

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.fipa_handler = cast(
            GenericFipaHandler, cls._skill.skill_context.handlers.fipa
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"transaction_digest": "some_transaction_digest_body"}},
            ),
        )

    def test_setup(self):
        """Test the setup method of the fipa handler."""
        assert self.fipa_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the fipa handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid fipa message={incoming_message}, unidentified dialogue.",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_propose_is_affordable_and_is_acceptable(self):
        """Test the _handle_propose method of the fipa handler."""
        # setup
        proposal = Description(
            {
                "ledger_id": self.strategy.ledger_id,
                "price": 100,
                "currency_id": "FET",
                "service_id": "some_service_id",
                "quantity": 1,
                "tx_nonce": "some_tx_nonce",
            }
        )
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )

        # operation
        with patch.object(
            self.strategy,
            "is_acceptable_proposal",
            return_value=True,
        ):
            with patch.object(
                self.strategy,
                "is_affordable_proposal",
                return_value=True,
            ):
                with patch.object(
                    self.fipa_handler.context.logger, "log"
                ) as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        incoming_message = cast(FipaMessage, incoming_message)
        mock_logger.assert_any_call(
            logging.INFO,
            f"received proposal={incoming_message.proposal.values} from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"accepting the proposal from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.ACCEPT,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

    def test_handle_propose_not_is_affordable_or_not_is_acceptable(self):
        """Test the _handle_propose method of the fipa handler."""
        # setup
        proposal = Description(
            {
                "ledger_id": self.strategy.ledger_id,
                "price": 100,
                "currency_id": "FET",
                "service_id": "some_service_id",
                "quantity": 1,
                "tx_nonce": "some_tx_nonce",
            }
        )
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=proposal,
        )

        # operation
        with patch.object(
            self.strategy,
            "is_acceptable_proposal",
            return_value=False,
        ):
            with patch.object(
                self.strategy,
                "is_affordable_proposal",
                return_value=False,
            ):
                with patch.object(
                    self.fipa_handler.context.logger, "log"
                ) as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        incoming_message = cast(FipaMessage, incoming_message)
        mock_logger.assert_any_call(
            logging.INFO,
            f"received proposal={incoming_message.proposal.values} from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"declining the proposal from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.DECLINE,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

    def test_handle_decline_decline_cfp(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_cfp."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.DECLINE,
        )

        # before
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received DECLINE from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_CFP:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_handle_decline_decline_accept(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_accept."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:3],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.DECLINE,
        )

        # before
        for end_state_numbers in list(
            self.fipa_dialogues.dialogue_stats.self_initiated.values()
        ) + list(self.fipa_dialogues.dialogue_stats.other_initiated.values()):
            assert end_state_numbers == 0

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received DECLINE from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.DECLINED_ACCEPT:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_handle_match_accept_is_ledger_tx(self):
        """Test the _handle_match_accept method of the fipa handler where is_ledger_tx is True."""
        # setup
        self.strategy._is_ledger_tx = True

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:3],
        )
        fipa_dialogue.terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                info={"info": {"address": "some_term_sender_address"}},
            ),
        )

        # operation
        with patch.object(
            self.fipa_handler.context.logger, "log"
        ) as mock_logger_handler:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger_handler.assert_any_call(
            logging.INFO,
            f"received MATCH_ACCEPT_W_INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]} with info={incoming_message.info}",
        )

        # operation
        with patch.object(
            self.fipa_handler.context.behaviours.transaction.context.logger, "log"
        ) as _:
            self.fipa_handler.context.behaviours.transaction.act()

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            terms=fipa_dialogue.terms,
        )
        assert has_attributes, error_str

    def test_handle_match_accept_not_is_ledger_tx(self):
        """Test the _handle_match_accept method of the fipa handler where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:3],
        )
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                info={"info": {"address": "some_term_sender_address"}},
            ),
        )

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received MATCH_ACCEPT_W_INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]} with info={incoming_message.info}",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            info={"Done": "Sending payment via bank transfer"},
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"informing counterparty={COUNTERPARTY_AGENT_ADDRESS[-5:]} of payment.",
        )

    def test_handle_inform_with_data(self):
        """Test the _handle_inform method of the fipa handler where info has data."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:4],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={"data_name": "data"},
        )

        # before
        for end_state_numbers in list(
            self.fipa_dialogues.dialogue_stats.self_initiated.values()
        ) + list(self.fipa_dialogues.dialogue_stats.other_initiated.values()):
            assert end_state_numbers == 0

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )
        mock_logger.assert_any_call(
            logging.INFO, "received the following data={'data_name': 'data'}"
        )

        for (
            end_state_numbers
        ) in self.fipa_dialogues.dialogue_stats.other_initiated.values():
            assert end_state_numbers == 0
        for (
            end_state,
            end_state_numbers,
        ) in self.fipa_dialogues.dialogue_stats.self_initiated.items():
            if end_state == FipaDialogue.EndState.SUCCESSFUL:
                assert end_state_numbers == 1
            else:
                assert end_state_numbers == 0

    def test_handle_inform_without_data(self):
        """Test the _handle_inform method of the fipa handler where info has NO data."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:4],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.INFORM,
            info={},
        )

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"received no data from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.fipa_handler.context.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle fipa message of performative={incoming_message.performative} in dialogue={fipa_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the fipa handler."""
        assert self.fipa_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestGenericOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of generic buyer."""

    path_to_skill = PACKAGE_ROOT
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            GenericOefSearchHandler, cls._skill.skill_context.handlers.oef_search
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES, {"query": "some_query"}
            ),
        )

    def test_setup(self):
        """Test the setup method of the oef_search handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )

    def test_handle_search_zero_agents(self):
        """Test the _handle_search method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=tuple(),
            agents_info=OefSearchMessage.AgentsInfo({}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"found no agents in dialogue={oef_dialogue}, continue searching.",
        )

    def test_handle_search_i(self):
        """Test the _handle_search method of the oef_search handler where is_stop_searching_on_result is True."""
        # setup
        self.strategy._max_negotiations = 3
        self.strategy._is_stop_searching_on_result = True
        self.strategy._is_searching = True

        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages[:1],
        )
        agents = ("agnt1", "agnt2")
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=agents,
            agents_info=OefSearchMessage.AgentsInfo(
                {"agent_1": {"key_1": "value_1"}, "agent_2": {"key_2": "value_2"}}
            ),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"found agents={list(agents)}, stopping search."
        )

        assert self.strategy.is_searching is False

        self.assert_quantity_in_outbox(len(agents))
        for agent in agents:
            has_attributes, error_str = self.message_has_attributes(
                actual_message=self.get_message_from_outbox(),
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                to=agent,
                sender=self.skill.skill_context.agent_address,
                target=0,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            mock_logger.assert_any_call(logging.INFO, f"sending CFP to agent={agent}")

    def test_handle_search_ii(self):
        """Test the _handle_search method of the oef_search handler where is_stop_searching_on_result is False."""
        # setup
        self.strategy._max_negotiations = 3
        self.strategy._is_stop_searching_on_result = False
        self.strategy._is_searching = True

        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages[:1],
        )
        agents = ("agnt1", "agnt2")
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=agents,
            agents_info=OefSearchMessage.AgentsInfo(
                {"agent_1": {"key_1": "value_1"}, "agent_2": {"key_2": "value_2"}}
            ),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, f"found agents={list(agents)}.")

        assert self.strategy.is_searching is True

        self.assert_quantity_in_outbox(len(agents))
        for agent in agents:
            has_attributes, error_str = self.message_has_attributes(
                actual_message=self.get_message_from_outbox(),
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                to=agent,
                sender=self.skill.skill_context.agent_address,
                target=0,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            mock_logger.assert_any_call(logging.INFO, f"sending CFP to agent={agent}")

    def test_handle_search_more_than_max_negotiation(self):
        """Test the _handle_search method of the oef_search handler where number of agents is more than max_negotiation."""
        # setup
        self.strategy._max_negotiations = 1
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages[:1],
        )
        agents = ("agnt1", "agnt2")
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=agents,
            agents_info=OefSearchMessage.AgentsInfo(
                {"agent_1": {"key_1": "value_1"}, "agent_2": {"key_2": "value_2"}}
            ),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"found agents={list(agents)}, stopping search."
        )

        assert not self.strategy.is_searching

        self.assert_quantity_in_outbox(self.strategy._max_negotiations)
        for idx in range(0, self.strategy._max_negotiations):
            has_attributes, error_str = self.message_has_attributes(
                actual_message=self.get_message_from_outbox(),
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                to=agents[idx],
                sender=self.skill.skill_context.agent_address,
                target=0,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            mock_logger.assert_any_call(
                logging.INFO, f"sending CFP to agent={agents[idx]}"
            )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef_search handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            service_description="some_service_description",
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle oef_search message of performative={invalid_performative} in dialogue={self.oef_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the oef_search handler."""
        assert self.oef_search_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestGenericSigningHandler(BaseSkillTestCase):
    """Test signing handler of generic buyer."""

    path_to_skill = PACKAGE_ROOT
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.signing_handler = cast(
            GenericSigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"transaction_digest": "some_transaction_digest_body"}},
            ),
        )
        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": cls.terms,
                    "raw_transaction": SigningMessage.RawTransaction(
                        "some_ledger_id", {"some_key": "some_value"}
                    ),
                },
            ),
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(LedgerApiMessage.Performative.GET_RAW_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.RAW_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.TRANSACTION_DIGEST, {}),
        )

    def test_setup(self):
        """Test the setup method of the signing handler."""
        assert self.signing_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=SigningMessage.Performative.ERROR,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.signing_handler.context.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid signing message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_signed_transaction_last_ledger_api_message_is_none(
        self,
    ):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
            ),
        )
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:2],
            ),
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        signing_dialogue.associated_ledger_api_dialogue._incoming_messages = []
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=signing_dialogue,
            performative=SigningMessage.Performative.SIGNED_TRANSACTION,
            signed_transaction=SigningMessage.SignedTransaction(
                "some_ledger_id", {"some_key": "some_value"}
            ),
        )

        # operation
        with pytest.raises(
            ValueError, match="Could not retrieve last message in ledger api dialogue"
        ):
            with patch.object(
                self.signing_handler.context.logger, "log"
            ) as mock_logger:
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "transaction signing was successful.")

    def test_handle_signed_transaction_last_ledger_api_message_is_not_none(
        self,
    ):
        """Test the _handle_signed_transaction method of the signing handler where the last ledger_api message is not None."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=signing_counterparty,
            ),
        )
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:2],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=SigningMessage.SignedTransaction(
                    "some_ledger_id", {"some_key": "some_value"}
                ),
            ),
        )
        # operation
        with patch.object(self.signing_handler.context.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "transaction signing was successful.")

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            signed_transaction=incoming_message.signed_transaction,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "sending transaction to ledger.")

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                counterparty=COUNTERPARTY_AGENT_ADDRESS,
                is_agent_to_agent_messages=True,
            ),
        )

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:4],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue

        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=signing_counterparty,
            ),
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.ERROR,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
            ),
        )

        # operation
        with patch.object(
            self.signing_handler.context.behaviours.transaction, "failed_processing"
        ):
            with patch.object(
                self.signing_handler.context.logger, "log"
            ) as mock_logger:
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction signing was not successful. Error_code={incoming_message.error_code} in dialogue={signing_dialogue}",
        )

        behaviour = cast(
            GenericTransactionBehaviour, self.skill.skill_context.behaviours.transaction
        )

        # finish_processing
        assert behaviour.processing_time == 0.0
        assert behaviour.processing is None

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the signing handler."""
        # setup
        invalid_performative = SigningMessage.Performative.SIGN_TRANSACTION
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            terms=self.terms,
            raw_transaction=SigningMessage.RawTransaction(
                "some_ledger_id", {"some_key": "some_value"}
            ),
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.signing_handler.context.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle signing message of performative={invalid_performative} in dialogue={self.signing_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the signing handler."""
        assert self.signing_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestGenericLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of generic buyer."""

    path_to_skill = PACKAGE_ROOT
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            GenericLedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.transaction_behaviour = cast(
            GenericTransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"transaction_digest": "some_transaction_digest_body"}},
            ),
        )
        cls.raw_transaction = RawTransaction(
            "some_ledger_id", {"some_key": "some_value"}
        )
        cls.signed_transaction = SignedTransaction(
            "some_ledger_id", {"some_key": "some_value"}
        )
        cls.transaction_digest = TransactionDigest("some_ledger_id", "some_body")
        cls.transaction_receipt = TransactionReceipt(
            "some_ledger_id",
            {"receipt_key": "receipt_value"},
            {"transaction_key": "transaction_value"},
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION, {"terms": cls.terms}
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.RAW_TRANSACTION,
                {"raw_transaction": cls.raw_transaction},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {"signed_transaction": cls.signed_transaction},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                {"transaction_digest": cls.transaction_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": cls.transaction_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                {"transaction_receipt": cls.transaction_receipt},
            ),
        )

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        assert self.ledger_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the ledger_api handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some_ledger_id",
            address="some_address",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_balance_positive_balance(self):
        """Test the _handle_balance method of the ledger_api handler where balance is positive."""
        # setup
        balance = 10
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": "some_ledger_id", "address": "some_address"},
                    ),
                ),
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id="some-Ledger_id",
                balance=balance,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"starting balance on {self.strategy.ledger_id} ledger={incoming_message.balance}.",
        )
        assert self.strategy.balance == balance
        assert self.strategy.is_searching

    def test_handle_balance_zero_balance(self):
        """Test the _handle_balance method of the ledger_api handler where balance is zero."""
        # setup
        balance = 0
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": "some_ledger_id", "address": "some_address"},
                    ),
                ),
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id="some-Ledger_id",
                balance=balance,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"you have no starting balance on {self.strategy.ledger_id} ledger! Stopping skill {self.strategy.context.skill_id}.",
        )
        assert not self.skill.skill_context.is_active

    def test_handle_raw_transaction(self):
        """Test the _handle_raw_transaction method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:1],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=self.raw_transaction,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received raw transaction={incoming_message}"
        )

        message_quantity = self.get_quantity_in_decision_maker_inbox()
        assert (
            message_quantity == 1
        ), f"Invalid number of messages in decision maker queue. Expected {1}. Found {message_quantity}."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_decision_maker_inbox(),
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
        )

    def test_handle_transaction_digest(self):
        """Test the _handle_transaction_digest method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:3],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=self.transaction_digest,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully submitted. Transaction digest={incoming_message.transaction_digest}",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            to=incoming_message.sender,
            sender=str(self.skill.skill_context.skill_id),
            transaction_digest=self.transaction_digest,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            "checking transaction is settled.",
        )

    def test_handle_transaction_receipt_i(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            self.ledger_api_handler.context.behaviours.transaction, "finish_processing"
        ):
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                with patch.object(self.logger, "log") as mock_logger:
                    self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction confirmed, informing counterparty={fipa_dialogue.dialogue_label.dialogue_opponent_addr[-5:]} of transaction digest.",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.INFORM,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            info={"transaction_digest": self.transaction_digest.body},
        )
        assert has_attributes, error_str

    def test_handle_transaction_receipt_ii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where fipa dialogue's last_incoming_message is None."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue

        fipa_dialogue._incoming_messages = []

        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            self.ledger_api_handler.context.behaviours.transaction, "finish_processing"
        ):
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                with patch.object(self.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Could not retrieve last fipa message"
                    ):
                        self.ledger_api_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

    def test_handle_transaction_receipt_iii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where tx is NOT settled."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        fipa_dialogue.terms = self.terms
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            self.ledger_api_handler.context.behaviours.transaction, "failed_processing"
        ):
            with patch.object(LedgerApis, "is_transaction_settled", return_value=False):
                with patch.object(self.logger, "log") as mock_logger:
                    self.ledger_api_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)
        assert self.transaction_behaviour.processing is None
        assert self.transaction_behaviour.processing_time == 0.0

        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction_receipt={self.transaction_receipt} not settled or not valid, aborting",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ledger_api_dialogues,
            messages=self.list_of_ledger_api_messages[:1],
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.ERROR,
                code=1,
            ),
        )
        ledger_api_dialogue.associated_fipa_dialogue = "mock"
        # operation
        with patch.object(
            self.ledger_api_handler.context.behaviours.transaction, "failed_processing"
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ledger_api error message={incoming_message} in dialogue={ledger_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the ledger_api handler."""
        # setup
        invalid_performative = LedgerApiMessage.Performative.GET_BALANCE
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id="some_ledger_id",
            address="some_address",
            to=str(self.skill.public_id),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ledger_api message of performative={invalid_performative} in dialogue={self.ledger_api_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the ledger_api handler."""
        assert self.ledger_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
