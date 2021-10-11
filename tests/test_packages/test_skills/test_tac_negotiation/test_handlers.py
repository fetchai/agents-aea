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
"""This module contains the tests of the handler classes of the tac negotiation skill."""

import logging
from pathlib import Path
from typing import Optional, cast
from unittest.mock import PropertyMock, patch

import pytest
from aea_ledger_ethereum import EthereumApi
from aea_ledger_fetchai import FetchAIApi

from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Query,
)
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedTransaction,
    State,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.protocols.dialogue.base import DialogueMessage, DialogueStats
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.cosm_trade.message import CosmTradeMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_negotiation.behaviours import (
    GoodsRegisterAndSearchBehaviour,
)
from packages.fetchai.skills.tac_negotiation.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    CosmTradeDialogue,
    CosmTradeDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.tac_negotiation.handlers import (
    ContractApiHandler,
    CosmTradeHandler,
    FipaNegotiationHandler,
    LEDGER_API_ADDRESS,
    LedgerApiHandler,
    OefSearchHandler,
    SigningHandler,
)
from packages.fetchai.skills.tac_negotiation.helpers import SUPPLY_DATAMODEL_NAME
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions

from tests.conftest import ROOT_DIR


class TestFipaHandler(BaseSkillTestCase):
    """Test fipa handler of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.fipa_handler = cast(
            FipaNegotiationHandler, cls._skill.skill_context.handlers.fipa
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.transactions = cast(Transactions, cls._skill.skill_context.transactions)
        cls.logger = cls._skill.skill_context.logger

        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )

        cls.dialogue_stats = cls.fipa_dialogues.dialogue_stats
        cls.ledger_id = "some_ledger_id"
        cls.counterprty_address = COUNTERPARTY_AGENT_ADDRESS
        cls.amount_by_currency_id = {"1": 50}
        cls.quantities_by_good_id = {"2": -10}
        cls.nonce = "234543"
        cls.contract_id = "some_contract_id"
        cls.contract_address = "some_contract_address"
        cls.kwargs = {"some_key": "some_value"}
        cls.counterparty_signature = "some_counterparty_signature"
        cls.terms = Terms(
            cls.ledger_id,
            cls._skill.skill_context.agent_address,
            cls.counterprty_address,
            cls.amount_by_currency_id,
            cls.quantities_by_good_id,
            cls.nonce,
        )
        cls.raw_message = RawMessage(
            ledger_id=cls.ledger_id, body=cls.terms.sender_hash.encode("utf-8")
        )

        cls.cfp_query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                SUPPLY_DATAMODEL_NAME,
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )
        cls.proposal = Description(
            {
                "ledger_id": cls.ledger_id,
                "price": 100,
                "currency_id": "1",
                "fee": 1,
                "nonce": cls.nonce,
            }
        )
        cls.list_of_messages_other_initiated = (
            DialogueMessage(
                FipaMessage.Performative.CFP, {"query": cls.cfp_query}, True
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.proposal}
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
        cls.list_of_messages_self_initiated = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": cls.cfp_query}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.proposal}
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
        with patch.object(self.logger, "log") as mock_logger:
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

    def _assert_stat_state(
        self,
        dialogue_stats: DialogueStats,
        changed_agent: Optional[str] = None,
        changed_end_state: Optional[FipaDialogue.EndState] = None,
    ) -> None:
        """
        Evaluates the state of dialogue stats.

        If 'changed_agent' and 'changed_end_state' are None,
        it asserts that the dialogue stats are 0 for all end_states.

        If they are not None, it checks that all end_states are 0, except for 'changed_end_state'
        in dialogues started by 'changed_agent' (i.e. 'self' or 'other').

        :param changed_agent: can either by 'self' or 'other'. Dialogues started by this agent has a none-zero end_state.
        :param changed_end_state: the changed end_state.
        :return:
        """
        if changed_agent is None and changed_end_state is None:
            unchanged_dict_1 = dialogue_stats.self_initiated
            unchanged_dict_2 = dialogue_stats.other_initiated
            for end_state_numbers in unchanged_dict_1.values():
                assert end_state_numbers == 0
            for end_state_numbers in unchanged_dict_2.values():
                assert end_state_numbers == 0
        elif changed_agent is not None and changed_end_state is not None:
            if changed_agent == "self":
                changed_dict = dialogue_stats.self_initiated
                unchanged_dict = dialogue_stats.other_initiated
            elif changed_agent == "other":
                changed_dict = dialogue_stats.other_initiated
                unchanged_dict = dialogue_stats.self_initiated
            else:
                raise SyntaxError(
                    f"changed_agent can only be 'self' or 'other'. Found {changed_agent}."
                )

            for end_state_numbers in unchanged_dict.values():
                assert end_state_numbers == 0
            for end_state, end_state_numbers in changed_dict.items():
                if end_state == changed_end_state:
                    assert end_state_numbers == 1
                else:
                    assert end_state_numbers == 0
        else:
            raise SyntaxError(
                "changed_agent and changed_end_state should either both be None, or neither."
            )

    def test_handle_cfp_i(self):
        """Test the _on_cfp method of the fipa handler where proposal_for_query is None."""
        # setup
        mocked_proposal = None
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            performative=FipaMessage.Performative.CFP,
            query=self.cfp_query,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(
            self.strategy, "get_proposal_for_query", return_value=mocked_proposal,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=FipaMessage,
            performative=FipaMessage.Performative.DECLINE,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

        self._assert_stat_state(
            self.dialogue_stats, "other", FipaDialogue.EndState.DECLINED_CFP
        )

    def test_handle_cfp_ii(self):
        """Test the _on_cfp method of the fipa handler where proposal_for_query is NOT None."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=FipaMessage,
            performative=FipaMessage.Performative.CFP,
            query=self.cfp_query,
        )

        # operation
        with patch.object(
            self.strategy, "get_proposal_for_query", return_value=self.proposal
        ):
            with patch.object(self.strategy, "terms_from_proposal") as mock_terms:
                with patch.object(
                    self.transactions, "add_pending_proposal"
                ) as mock_pending:
                    with patch.object(self.logger, "log") as mock_logger:
                        self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.PROPOSE,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            proposal=self.proposal,
        )
        assert has_attributes, error_str

        mock_terms.assert_called_once()
        mock_pending.assert_called_once()

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative} to {message.to[-5:]} (as {self.fipa_dialogues.get_dialogue(message).role}), message={message}",
        )

    def test_handle_propose_i(self):
        """Test the _handle_propose method of the fipa handler where the tx IS profitable."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages_self_initiated[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=self.proposal,
        )

        # operation
        with patch.object(
            self.strategy, "is_profitable_transaction", return_value=True
        ):
            with patch.object(self.transactions, "add_locked_tx") as mock_lock:
                with patch.object(
                    self.transactions, "add_pending_initial_acceptance"
                ) as mock_pending:
                    with patch.object(self.logger, "log") as mock_logger:
                        self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.ACCEPT,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

        mock_lock.assert_called_once()
        mock_pending.assert_called_once()

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative} to {message.to[-5:]} (as {self.fipa_dialogues.get_dialogue(message).role}), message={message}",
        )

    def test_handle_propose_ii(self):
        """Test the _handle_propose method of the fipa handler where the tx is NOT profitable."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages_self_initiated[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=self.proposal,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(
            self.strategy, "is_profitable_transaction", return_value=False
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.DECLINE,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

        self._assert_stat_state(
            self.dialogue_stats, "self", FipaDialogue.EndState.DECLINED_PROPOSE
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative} to {message.to[-5:]} (as {self.fipa_dialogues.get_dialogue(message).role}), message={message}",
        )

    def test_handle_decline_decline_cfp(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_cfp."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages_self_initiated[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.DECLINE,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        self._assert_stat_state(
            self.dialogue_stats, "self", FipaDialogue.EndState.DECLINED_CFP
        )

    def test_handle_decline_decline_propose(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_propose."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages_other_initiated[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.DECLINE,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(self.transactions, "pop_pending_proposal") as mock_pending:
            with patch.object(self.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        self._assert_stat_state(
            self.dialogue_stats, "other", FipaDialogue.EndState.DECLINED_PROPOSE
        )

        mock_pending.assert_called_once()

    def test_handle_decline_decline_accept(self):
        """Test the _handle_decline method of the fipa handler where the end state is decline_accept."""
        # setup
        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages_self_initiated[:3],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.DECLINE,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(
            self.transactions, "pop_pending_initial_acceptance"
        ) as mock_pending:
            with patch.object(self.transactions, "pop_locked_tx") as mock_locked:
                with patch.object(self.logger, "log") as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        self._assert_stat_state(
            self.dialogue_stats, "self", FipaDialogue.EndState.DECLINED_ACCEPT
        )

        mock_pending.assert_called_once()
        mock_locked.assert_called_once()

    def test_handle_accept_i(self):
        """Test the _on_accept method of the fipa handler where the tx IS profitable, is_contract_tx is True, ledger is Ethereum."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = EthereumApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_other_initiated[:2],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.transactions, "pop_pending_proposal") as mock_pending:
            with patch.object(
                self.strategy, "is_profitable_transaction", return_value=True
            ):
                with patch.object(self.transactions, "add_locked_tx") as mock_lock:
                    with patch.object(
                        type(self.strategy),
                        "contract_id",
                        new_callable=PropertyMock,
                        return_value=self.contract_id,
                    ):
                        with patch.object(
                            type(self.strategy),
                            "contract_address",
                            new_callable=PropertyMock,
                            return_value=self.contract_address,
                        ):
                            with patch.object(
                                self.strategy,
                                "kwargs_from_terms",
                                return_value=self.kwargs,
                            ):
                                with patch.object(self.logger, "log") as mock_logger:
                                    self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_pending.assert_called_once()
        mock_lock.assert_called_once()

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=EthereumApi.identifier,
            contract_id=self.contract_id,
            contract_address=self.contract_address,
            callable="get_hash_batch",
            kwargs=ContractApiMessage.Kwargs(self.kwargs),
        )
        assert has_attributes, error_str

        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting batch transaction hash, sending {message.performative} to {self.contract_id}, message={message}",
        )

    def test_handle_accept_ii(self):
        """Test the _on_accept method of the fipa handler where the tx IS profitable and strategy's is_contract_tx is False."""
        # setup
        self.strategy._is_contract_tx = False

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_other_initiated[:2],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(
            self.transactions, "pop_pending_proposal", return_value=self.terms
        ) as mock_pending:
            with patch.object(
                self.strategy, "is_profitable_transaction", return_value=True
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_decision_making_queue(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_pending.assert_called_once()

        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
            raw_message=self.raw_message,
        )
        assert has_attributes, error_str

        assert (
            cast(
                SigningDialogue, self.signing_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting signature, sending {message.performative} to decision_maker, message={message}",
        )

    def test_handle_accept_iii(self):
        """Test the _on_accept method of the fipa handler where the tx IS profitable, is_contract_tx is True, ledger is FetchAi."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_other_initiated[:2],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.transactions, "pop_pending_proposal") as mock_pending:
            with patch.object(
                self.strategy, "is_profitable_transaction", return_value=True
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_pending.assert_called_once()

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            info={
                "public_key": self.skill.skill_context.public_keys[
                    self.strategy.ledger_id
                ]
            },
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative.value} to {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={message}.",
        )

    def test_handle_accept_iv(self):
        """Test the _on_accept method of the fipa handler where the tx IS profitable, is_contract_tx is True, ledger is FetchAi, public_key is None."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_other_initiated[:2],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.transactions, "pop_pending_proposal") as mock_pending:
            with patch.object(
                self.strategy, "is_profitable_transaction", return_value=True
            ):
                with patch.object(
                    type(self.strategy),
                    "contract_address",
                    new_callable=PropertyMock,
                    return_value=self.contract_address,
                ):
                    with patch.object(
                        type(self.skill.skill_context),
                        "public_keys",
                        new_callable=PropertyMock,
                        return_value={"some_ledger": "some_public_key"},
                    ):
                        with patch.object(self.logger, "log") as mock_logger:
                            self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_pending.assert_called_once()

        mock_logger.assert_any_call(
            logging.INFO, f"Agent has no public key for {self.strategy.ledger_id}.",
        )

    def test_handle_accept_v(self):
        """Test the _on_accept method of the fipa handler where the tx IS profitable, is_contract_tx is True, ledger is not FetchAi nor Ethereum."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = self.ledger_id

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_other_initiated[:2],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # operation
        with patch.object(self.transactions, "pop_pending_proposal") as mock_pending:
            with patch.object(
                self.strategy, "is_profitable_transaction", return_value=True
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    with pytest.raises(
                        AEAEnforceError,
                        match=f"Unidentified ledger id: {self.ledger_id}",
                    ):
                        self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )
        mock_pending.assert_called_once()

    def test_handle_accept_vi(self):
        """Test the _on_accept method of the fipa handler where the tx is NOT profitable."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_other_initiated[:2],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(
            self.transactions, "pop_pending_proposal", return_value=self.terms
        ) as mock_pending:
            with patch.object(
                self.strategy, "is_profitable_transaction", return_value=False
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_pending.assert_called_once()

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.DECLINE,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
        )
        assert has_attributes, error_str

        self._assert_stat_state(
            self.dialogue_stats, "other", FipaDialogue.EndState.DECLINED_ACCEPT
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative} to {message.to[-5:]} (as {self.fipa_dialogues.get_dialogue(message).role}), message={message}",
        )

    def test_handle_match_accept_i(self):
        """Test the _handle_match_accept method of the fipa handler where is_contract_tx is True and ledger_id is Fetchai."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_self_initiated[:3],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={},
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"{incoming_message.performative} did not contain counterparty public_key!",
        )

    def test_handle_match_accept_ii(self):
        """Test the _handle_match_accept method of the fipa handler where is_contract_tx is True and ledger_id is Fetchai."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier
        counterparty_public_key = "counterparty_public_key"

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_self_initiated[:3],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"public_key": counterparty_public_key},
        )

        # operation
        with patch.object(
            type(self.strategy),
            "contract_address",
            new_callable=PropertyMock,
            return_value=self.contract_address,
        ):
            with patch.object(
                type(self.strategy),
                "contract_id",
                new_callable=PropertyMock,
                return_value=self.contract_id,
            ):
                with patch.object(
                    self.strategy, "kwargs_from_terms", return_value=self.kwargs
                ):
                    with patch.object(self.logger, "log") as mock_logger:
                        self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=FetchAIApi.identifier,
            contract_id=self.contract_id,
            contract_address=self.contract_address,
            callable="get_atomic_swap_batch_transaction",
            kwargs=ContractApiMessage.Kwargs(self.kwargs),
        )
        assert has_attributes, error_str

        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting batch atomic swap transaction, sending {message.performative} to {self.contract_id}, message={message}",
        )

    def test_handle_match_accept_iii(self):
        """Test the _handle_match_accept method of the fipa handler where is_contract_tx is True and ledger_id is neither Fetchai nor Ethereum."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = self.ledger_id

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_self_initiated[:3],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={},
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(
                AEAEnforceError, match=f"Unidentified ledger id: {self.ledger_id}"
            ):
                self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

    def test_handle_match_accept_iv(self):
        """Test the _handle_match_accept method of the fipa handler where is_contract_tx is True, ledger_id is Ethereum and counterparty signature is None."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = EthereumApi.identifier

        fipa_dialogue = self.prepare_skill_dialogue(
            dialogues=self.fipa_dialogues,
            messages=self.list_of_messages_self_initiated[:3],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"signature": None},
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"{incoming_message.performative} did not contain counterparty signature!",
        )

    def test_handle_match_accept_v(self):
        """Test the _handle_match_accept method of the fipa handler where is_contract_tx is True and counterparty signature is NOT None."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = EthereumApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_self_initiated[:3],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"signature": self.counterparty_signature},
        )

        # operation
        with patch.object(
            type(self.strategy),
            "contract_id",
            new_callable=PropertyMock,
            return_value=self.contract_id,
        ):
            with patch.object(
                type(self.strategy),
                "contract_address",
                new_callable=PropertyMock,
                return_value=self.contract_address,
            ):
                with patch.object(
                    self.strategy, "kwargs_from_terms", return_value=self.kwargs
                ):
                    with patch.object(self.logger, "log") as mock_logger:
                        self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        assert fipa_dialogue.counterparty_signature == self.counterparty_signature

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=EthereumApi.identifier,
            contract_id=self.contract_id,
            contract_address=self.contract_address,
            callable="get_atomic_swap_batch_transaction",
            kwargs=ContractApiMessage.Kwargs(self.kwargs),
        )
        assert has_attributes, error_str

        assert (
            cast(
                ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting batch atomic swap transaction, sending {message.performative} to {self.contract_id}, message={message}",
        )

    def test_handle_match_accept_vi(self):
        """Test the _handle_match_accept method of the fipa handler where is_contract_tx is False and counterparty signature is NOT None."""
        # setup
        self.strategy._is_contract_tx = False

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_messages_self_initiated[:3],
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=fipa_dialogue,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            info={"signature": self.counterparty_signature},
        )

        # operation
        with patch.object(
            self.transactions, "pop_pending_initial_acceptance", return_value=self.terms
        ) as mock_pending:
            with patch.object(self.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_decision_making_queue(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from {incoming_message.sender[-5:]} (as {self.fipa_dialogues.get_dialogue(incoming_message).role}), message={incoming_message}",
        )

        mock_pending.assert_called_once()

        assert fipa_dialogue.counterparty_signature == self.counterparty_signature

        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
            raw_message=self.raw_message,
        )
        assert has_attributes, error_str

        assert (
            cast(
                SigningDialogue, self.signing_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"requesting signature, sending {message.performative} to decision_maker, message={message}",
        )

    def test_teardown(self):
        """Test the teardown method of the fipa handler."""
        assert self.fipa_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestCosmTradeHandler(BaseSkillTestCase):
    """Test cosm_trade handler of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.cosm_trade_handler = cast(
            CosmTradeHandler, cls._skill.skill_context.handlers.cosm_trade
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.cosm_trade_dialogues = cast(
            CosmTradeDialogues, cls._skill.skill_context.cosm_trade_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )

        cls.dialogue_stats = cls.cosm_trade_dialogues.dialogue_stats
        cls.ledger_id = "some_ledger_id"
        cls.counterprty_address = COUNTERPARTY_AGENT_ADDRESS
        cls.amount_by_currency_id = {"1": 50}
        cls.quantities_by_good_id = {"2": -10}
        cls.nonce = "234543"
        cls.body = {"some_key": "some_value"}
        cls.fipa_dialogue_id = ("1", "1")
        cls.terms = Terms(
            cls.ledger_id,
            cls._skill.skill_context.agent_address,
            cls.counterprty_address,
            cls.amount_by_currency_id,
            cls.quantities_by_good_id,
            cls.nonce,
        )
        cls.raw_message = RawMessage(
            ledger_id=cls.ledger_id, body=cls.terms.sender_hash.encode("utf-8")
        )
        cls.signed_tx = SignedTransaction(cls.ledger_id, cls.body)

        cls.cfp_query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                SUPPLY_DATAMODEL_NAME,
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )
        cls.proposal = Description(
            {
                "ledger_id": cls.ledger_id,
                "price": 100,
                "currency_id": "1",
                "fee": 1,
                "nonce": cls.nonce,
            }
        )
        cls.list_of_fipa_messages = (
            DialogueMessage(
                FipaMessage.Performative.CFP, {"query": cls.cfp_query}, True
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.proposal}
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
        cls.list_of_cosm_trade_messages = (
            DialogueMessage(
                CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION,
                {"signed_transaction": cls.signed_tx, "fipa_dialogue_id": ("1", "")},
            ),
        )

    @staticmethod
    def _assert_stat_state(
        dialogue_stats: DialogueStats,
        changed_agent: Optional[str] = None,
        changed_end_state: Optional[CosmTradeDialogue.EndState] = None,
    ) -> None:
        """
        Evaluates the state of dialogue stats.

        If 'changed_agent' and 'changed_end_state' are None,
        it asserts that the dialogue stats are 0 for all end_states.

        If they are not None, it checks that all end_states are 0, except for 'changed_end_state'
        in dialogues started by 'changed_agent' (i.e. 'self' or 'other').

        :param changed_agent: can either by 'self' or 'other'. Dialogues started by this agent has a none-zero end_state.
        :param changed_end_state: the changed end_state.
        :return:
        """
        if changed_agent is None and changed_end_state is None:
            unchanged_dict_1 = dialogue_stats.self_initiated
            unchanged_dict_2 = dialogue_stats.other_initiated
            for end_state_numbers in unchanged_dict_1.values():
                assert end_state_numbers == 0
            for end_state_numbers in unchanged_dict_2.values():
                assert end_state_numbers == 0
        elif changed_agent is not None and changed_end_state is not None:
            if changed_agent == "self":
                changed_dict = dialogue_stats.self_initiated
                unchanged_dict = dialogue_stats.other_initiated
            elif changed_agent == "other":
                changed_dict = dialogue_stats.other_initiated
                unchanged_dict = dialogue_stats.self_initiated
            else:
                raise SyntaxError(
                    f"changed_agent can only be 'self' or 'other'. Found {changed_agent}."
                )

            for end_state_numbers in unchanged_dict.values():
                assert end_state_numbers == 0
            for end_state, end_state_numbers in changed_dict.items():
                if end_state == changed_end_state:
                    assert end_state_numbers == 1
                else:
                    assert end_state_numbers == 0
        else:
            raise SyntaxError(
                "changed_agent and changed_end_state should either both be None, or neither."
            )

    def test_setup(self):
        """Test the setup method of the cosm_trade handler."""
        assert self.cosm_trade_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the cosm_trade handler."""
        # setup
        self.strategy._is_contract_tx = True
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=CosmTradeMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=CosmTradeMessage.Performative.INFORM_PUBLIC_KEY,
            public_key="some_public_key",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.cosm_trade_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid cosm_trade message={incoming_message}, unidentified dialogue.",
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
            error_data={"cosm_trade_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_signed_tx_i(self):
        """Test the _on_accept method of the cosm_trade handler."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message(
            message_type=CosmTradeMessage,
            performative=CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION,
            signed_transaction=self.signed_tx,
            fipa_dialogue_id=fipa_dialogue.dialogue_label.dialogue_reference,
        )

        raw_tx = RawTransaction(
            ledger_id=self.signed_tx.ledger_id, body=self.signed_tx.body,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.cosm_trade_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_decision_making_queue(1)

        mock_logger.assert_any_call(
            logging.INFO, f"received inform_signed_tx with signed_tx={self.signed_tx}",
        )

        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
            raw_transaction=raw_tx,
        )
        assert has_attributes, error_str

        assert (
            cast(
                SigningDialogue, self.signing_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )
        assert cast(
            SigningDialogue, self.signing_dialogues.get_dialogue(message)
        ).associated_cosm_trade_dialogue == self.cosm_trade_dialogues.get_dialogue(
            incoming_message
        )

        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
        )

    def test_handle_signed_tx_ii(self):
        """Test the _on_accept method of the cosm_trade handler where fipa_dialogue_id IS None."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._terms = self.terms
        incoming_message = self.build_incoming_message(
            message_type=CosmTradeMessage,
            performative=CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION,
            signed_transaction=self.signed_tx,
            fipa_dialogue_id=None,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.cosm_trade_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_decision_making_queue(0)

        mock_logger.assert_any_call(
            logging.INFO, f"received inform_signed_tx with signed_tx={self.signed_tx}",
        )

        mock_logger.assert_any_call(
            logging.INFO, "inform_signed_tx must contain fipa dialogue reference.",
        )

    def test_handle_error(self):
        """Test the _handle_decline method of the cosm_trade handler where the end state is Failed."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier
        cosm_trade_dialogue = self.prepare_skill_dialogue(
            dialogues=self.cosm_trade_dialogues,
            messages=self.list_of_cosm_trade_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=cosm_trade_dialogue,
            performative=CosmTradeMessage.Performative.ERROR,
            code=1,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.cosm_trade_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received cosm_trade_api error message={incoming_message} in dialogue={cosm_trade_dialogue}.",
        )

        self._assert_stat_state(
            self.dialogue_stats, "self", CosmTradeDialogue.EndState.FAILED
        )

    def test_handle_end(self):
        """Test the _handle_decline method of the cosm_trade handler where the end state is SUCCESS."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier
        cosm_trade_dialogue = self.prepare_skill_dialogue(
            dialogues=self.cosm_trade_dialogues,
            messages=self.list_of_cosm_trade_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=cosm_trade_dialogue,
            performative=CosmTradeMessage.Performative.END,
        )

        # before
        self._assert_stat_state(self.dialogue_stats)

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.cosm_trade_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received cosm_trade_api end message={incoming_message} in dialogue={cosm_trade_dialogue}.",
        )

        self._assert_stat_state(
            self.dialogue_stats, "self", CosmTradeDialogue.EndState.SUCCESSFUL
        )

    def test_teardown(self):
        """Test the teardown method of the cosm_trade handler."""
        assert self.cosm_trade_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestSigningHandler(BaseSkillTestCase):
    """Test signing handler of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls.signing_handler.context.logger

        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.cosm_trade_dialogues = cast(
            CosmTradeDialogues, cls._skill.skill_context.cosm_trade_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.ledger_id = "some_ledger_id"
        cls.nonce = "some_nonce"
        cls.body = {"some_key": "some_value"}
        cls.body_bytes = b"some_body"
        cls.body_str = "some_body"
        cls.counterparty_signature = "some_counterparty_signature"
        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_signing_msg_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_MESSAGE,
                {
                    "terms": cls.terms,
                    "raw_message": SigningMessage.RawMessage(
                        cls.ledger_id, cls.body_bytes
                    ),
                },
            ),
        )
        cls.list_of_signing_tx_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": cls.terms,
                    "raw_transaction": SigningMessage.RawTransaction(
                        cls.ledger_id, cls.body
                    ),
                },
            ),
        )

        cls.cfp_query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                SUPPLY_DATAMODEL_NAME,
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )
        cls.proposal = Description(
            {
                "ledger_id": cls.ledger_id,
                "price": 100,
                "currency_id": "1",
                "fee": 1,
                "nonce": cls.nonce,
            }
        )
        cls.list_of_other_initiated_fipa_messages = (
            DialogueMessage(
                FipaMessage.Performative.CFP, {"query": cls.cfp_query}, True
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.proposal}
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
        cls.list_of_self_initiated_fipa_messages_ethereum = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": cls.cfp_query}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.proposal}
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
        cls.list_of_self_initiated_fipa_messages_fetchai = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": cls.cfp_query}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.proposal}
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                {"info": {"address": "some_term_sender_address"}},
            ),
            DialogueMessage(
                FipaMessage.Performative.INFORM,
                {"info": {"public_key": "some_public_key"}},
            ),
        )

        cls.signed_tx = SignedTransaction(cls.ledger_id, cls.body)

        cls.list_of_cosm_trade_messages = (
            DialogueMessage(
                CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION,
                {"signed_transaction": cls.signed_tx, "fipa_dialogue_id": ("1", "")},
            ),
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
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid signing message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_signed_message_i(self):
        """Test the _handle_signed_message method of the signing handler where last fipa message is ACCEPT."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_other_initiated_fipa_messages[:3],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_msg_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SigningMessage.SignedMessage(
                    self.ledger_id, self.body_str
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            to=fipa_dialogue.dialogue_label.dialogue_opponent_addr,
            # (line below) match-accept is already added to fipa_dialogue, hence "-1"
            target=fipa_dialogue.last_incoming_message.message_id,
            sender=self.skill.skill_context.agent_address,
            info={"signature": incoming_message.signed_message.body},
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative.value} to {message.to[-5:]} (as {fipa_dialogue.role}), message={message}.",
        )

    def test_handle_signed_message_ii(self):
        """Test the _handle_signed_message method of the signing handler where last fipa message is MATCH_ACCEPT."""
        # setup
        mocked_tx = {
            "terms": self.terms,
            "sender_signature": self.body_str,
            "counterparty_signature": self.counterparty_signature,
        }

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_ethereum[:4],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue.counterparty_signature = self.counterparty_signature
        fipa_dialogue.terms = self.terms

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_msg_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SigningMessage.SignedMessage(
                    self.ledger_id, self.body_str
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        assert (
            self.skill.skill_context.shared_state["transactions"][
                fipa_dialogue.terms.sender_hash
            ]
            == mocked_tx
        )

        mock_logger.assert_any_call(
            logging.INFO, f"sending transaction to controller, tx={mocked_tx}."
        )

    def test_handle_signed_message_iii(self):
        """Test the _handle_signed_message method of the signing handler where last fipa message is neither ACCEPT nor MATCH_ACCEPT."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_ethereum[:3],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_msg_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SigningMessage.SignedMessage(
                    self.ledger_id, self.body_str
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(
                AEAEnforceError,
                match="last message should be of performative accept or match accept.",
            ):
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

    def test_handle_signed_message_iv(self):
        """Test the _handle_signed_message method of the signing handler where last fipa message is None."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_ethereum[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._incoming_messages = []
        fipa_dialogue._outgoing_messages = []

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_msg_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SigningMessage.SignedMessage(
                    self.ledger_id, self.body_str
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(AEAEnforceError, match="last message not recovered."):
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

    def test_handle_signed_transaction_v(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is False."""
        # setup
        self.strategy._is_contract_tx = False

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        mock_logger.assert_any_call(
            logging.WARNING, "signed transaction handler only for contract case."
        )

    def test_handle_signed_transaction_vi(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True, associated cosm_trade dialogue is NOT None."""
        # setup
        self.strategy._is_contract_tx = True

        cosm_trade_dialogue = cast(
            CosmTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.cosm_trade_dialogues,
                messages=self.list_of_cosm_trade_messages,
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_cosm_trade_dialogue = cosm_trade_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            signed_transaction=incoming_message.signed_transaction,
        )
        assert has_attributes, error_str

        assert (
            cast(
                LedgerApiDialogue, self.ledger_api_dialogues.get_dialogue(message)
            ).associated_signing_dialogue
            == signing_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative} to ledger {self.strategy.ledger_id}, message={message}",
        )

    def test_handle_signed_transaction_i(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True and last fipa message is ACCEPT."""
        # setup
        self.strategy._is_contract_tx = True

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_other_initiated_fipa_messages[:3],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            to=fipa_dialogue.dialogue_label.dialogue_opponent_addr,
            # (line below) match-accept is already added to fipa_dialogue, hence "-1"
            sender=self.skill.skill_context.agent_address,
            info={"tx_signature": incoming_message.signed_transaction},
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative.value} to {message.to[-5:]} (as {fipa_dialogue.role}), message={message}.",
        )

    def test_handle_signed_transaction_ii(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True and last fipa message is MATCH_ACCEPT and ledger is Ethereum."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = EthereumApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_ethereum[:4],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            signed_transaction=incoming_message.signed_transaction,
        )
        assert has_attributes, error_str

        assert (
            cast(
                LedgerApiDialogue, self.ledger_api_dialogues.get_dialogue(message)
            ).associated_signing_dialogue
            == signing_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative} to ledger {self.strategy.ledger_id}, message={message}",
        )

    def test_handle_signed_transaction_vii(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True and last fipa message is MATCH_ACCEPT and ledger is Fetchai."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = FetchAIApi.identifier

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_fetchai[:4],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=CosmTradeMessage,
            performative=CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION,
            to=fipa_dialogue.dialogue_label.dialogue_opponent_addr,
            sender=self.skill.skill_context.agent_address,
            signed_transaction=incoming_message.signed_transaction,
            fipa_dialogue_id=fipa_dialogue.dialogue_label.dialogue_reference,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending {message.performative.value} to {message.to[-5:]}, message={message}.",
        )

    def test_handle_signed_transaction_viii(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True and last fipa message is MATCH_ACCEPT and ledger is neither Ethereum nor Fetchai."""
        # setup
        self.strategy._is_contract_tx = True
        self.strategy._ledger_id = self.ledger_id

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_fetchai[:4],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(
                AEAEnforceError, match=f"Unidentified ledger id: {self.ledger_id}",
            ):
                self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

    def test_handle_signed_transaction_iii(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True and last fipa message is neither ACCEPT nor MATCH_ACCEPT."""
        # setup
        self.strategy._is_contract_tx = True

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_ethereum[:3],
                is_agent_to_agent_messages=True,
            ),
        )

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(
                AEAEnforceError,
                match="last message should be of performative accept or match accept.",
            ):
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

    def test_handle_signed_transaction_iv(self):
        """Test the _handle_signed_transaction method of the signing handler where is_contract_tx is True and last incoming fipa message is None."""
        # setup
        self.strategy._is_contract_tx = True

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_self_initiated_fipa_messages_ethereum[:3],
                is_agent_to_agent_messages=True,
            ),
        )
        fipa_dialogue._incoming_messages = []
        fipa_dialogue._outgoing_messages = []

        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_tx_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.signed_tx,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(AEAEnforceError, match="last message not recovered."):
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = self.prepare_skill_dialogue(
            dialogues=self.signing_dialogues,
            messages=self.list_of_signing_tx_messages[:1],
            counterparty=signing_counterparty,
        )
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.ERROR,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction signing was not successful. Error_code={incoming_message.error_code} in dialogue={signing_dialogue}",
        )

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
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received {incoming_message.performative} from decision_maker, message={incoming_message}",
        )

        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle signing message of performative={invalid_performative} in dialogue={self.signing_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the signing handler."""
        assert self.signing_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.logger = cls.ledger_api_handler.context.logger

        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.ledger_id = "some_ledger_id"
        cls.contract_id = "some_contract_id"
        cls.callable = "some_callable"
        cls.kwargs = Kwargs({"some_key": "some_value"})

        cls.body = {"some_key": "some_value"}
        cls.body_str = "some_body"
        cls.contract_address = "some_contract_address"

        cls.raw_transaction = RawTransaction(cls.ledger_id, cls.body)
        cls.signed_transaction = SignedTransaction(cls.ledger_id, cls.body)
        cls.transaction_digest = TransactionDigest(cls.ledger_id, cls.body_str)
        cls.receipt = {"contractAddress": cls.contract_address}
        cls.transaction_receipt = TransactionReceipt(
            cls.ledger_id, cls.receipt, {"transaction_key": "transaction_value"}
        )
        cls.address = "some_address"

        cls.terms = Terms(
            cls.ledger_id,
            cls._skill.skill_context.agent_address,
            "counterparty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
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
            performative=LedgerApiMessage.Performative.BALANCE,
            ledger_id="some_ledger_id",
            balance=10,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_balance(self):
        """Test the _handle_balance method of the ledger_api handler."""
        # setup
        balance = 10
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": self.ledger_id, "address": self.address},
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
                ledger_id=self.ledger_id,
                balance=balance,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"starting balance on {self.ledger_id} ledger={incoming_message.balance}.",
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
            target=incoming_message.message_id,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            transaction_digest=incoming_message.transaction_digest,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "requesting transaction receipt.")

    def test_handle_transaction_receipt_failed(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where the transaction is NOT settled."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(LedgerApis, "is_transaction_settled", return_value=False):
            with patch.object(self.logger, "log") as mock_logger:
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.ERROR,
            f"transaction failed. Transaction receipt={incoming_message.transaction_receipt}",
        )

    def test_handle_transaction_receipt_succeeds(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where the transaction is NOT settled."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
            with patch.object(self.logger, "log") as mock_logger:
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={incoming_message.transaction_receipt}",
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

        # operation
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
            address=self.address,
            to=str(self.skill.skill_context.skill_id),
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


class TestOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger
        cls.service_registration_behaviour = cast(
            GoodsRegisterAndSearchBehaviour,
            cls._skill.skill_context.behaviours.tac_negotiation,
        )

        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )

        cls.controller_address = "some_controller_address"
        cls.self_address = cls._skill.skill_context.agent_address
        cls.found_agent_address_1 = "some_agent_address_1"
        cls.found_agent_address_2 = "some_agent_address_2"
        cls.found_agent_address_3 = "some_agent_address_3"
        cls.found_agents = [
            cls.self_address,
            cls.found_agent_address_1,
            cls.found_agent_address_2,
            cls.found_agent_address_3,
        ]
        cls.found_agents_less_self = [
            cls.found_agent_address_1,
            cls.found_agent_address_2,
            cls.found_agent_address_3,
        ]
        cls.cfp_query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                SUPPLY_DATAMODEL_NAME,
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )

        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES, {"query": "some_query"}
            ),
        )

        cls.register_location_description = Description(
            {"location": Location(51.5194, 0.1270)},
            data_model=DataModel(
                "location_agent", [Attribute("location", Location, True)]
            ),
        )
        cls.list_of_messages_register_location = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_location_description},
                is_incoming=False,
            ),
        )

        cls.register_service_description = Description(
            {"key": "some_key", "value": "some_value"},
            data_model=DataModel(
                "set_service_key",
                [Attribute("key", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_service = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_service_description},
                is_incoming=False,
            ),
        )

        cls.register_genus_description = Description(
            {"piece": "genus", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_genus = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_genus_description},
                is_incoming=False,
            ),
        )

        cls.register_classification_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_classification = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_classification_description},
                is_incoming=False,
            ),
        )

        cls.register_invalid_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "some_different_name",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_invalid = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_invalid_description},
                is_incoming=False,
            ),
        )

        cls.unregister_description = Description(
            {"key": "seller_service"},
            data_model=DataModel("remove", [Attribute("key", str, True)]),
        )
        cls.list_of_messages_unregister = (
            DialogueMessage(
                OefSearchMessage.Performative.UNREGISTER_SERVICE,
                {"service_description": cls.unregister_description},
                is_incoming=False,
            ),
        )

    def test_setup(self):
        """Test the setup method of the oef handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_success_i(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH location_agent data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.service_registration_behaviour.is_registered is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_service",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()
        assert self.service_registration_behaviour.is_registered is False

    def test_handle_success_ii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH set_service_key data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_service[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.service_registration_behaviour.is_registered is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_genus",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()
        assert self.service_registration_behaviour.is_registered is False

    def test_handle_success_iii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and genus value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_genus[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.service_registration_behaviour.is_registered is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_classification",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()
        assert self.service_registration_behaviour.is_registered is False

    def test_handle_success_iv(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and classification value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_classification[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.service_registration_behaviour.is_registered is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            "the agent, with its genus and classification, and its service are successfully registered on the SOEF.",
        )
        assert self.service_registration_behaviour.is_registered is True

    def test_handle_success_v(self):
        """Test the _handle_success method of the oef_search handler where the oef successtargets unregister_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_invalid[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # before
        assert self.service_registration_behaviour.is_registered is False

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received soef SUCCESS message as a reply to the following unexpected message: {oef_dialogue.get_message_by_id(incoming_message.target)}",
        )
        assert self.service_registration_behaviour.is_registered is False

    def test_on_oef_error_i(self):
        """Test the _handle_error method of the oef_search handler where the oef error targets register_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.OEF_ERROR,
                oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
            ),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.WARNING,
            f"received OEF Search error: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference}, oef_error_operation={incoming_message.oef_error_operation}",
        )
        assert (
            self.service_registration_behaviour.failed_registration_msg
            == oef_dialogue.get_message_by_id(incoming_message.target)
        )

    def test_on_oef_error_ii(self):
        """Test the _handle_error method of the oef_search handler where the oef error does NOT target register_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages_unregister[:1],
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
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.WARNING,
            f"received OEF Search error: dialogue_reference={oef_dialogue.dialogue_label.dialogue_reference}, oef_error_operation={incoming_message.oef_error_operation}",
        )

        assert self.service_registration_behaviour.failed_registration_msg is None

    def test_on_search_result_i(self):
        """Test the _on_search_result method of the oef handler."""
        # setup
        oef_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
            ),
        )
        oef_dialogue._is_seller_search = True
        search_for = "sellers"

        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                to=str(self.skill.skill_context.skill_id),
                agents=tuple(self.found_agents),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(
                self.strategy, "get_own_services_query", return_value=self.cfp_query
            ) as mock_own:
                self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(len(self.found_agents_less_self))

        # _handle_search
        mock_logger.assert_any_call(
            logging.INFO,
            f"found potential {search_for} agents={list(map(lambda x: x[-5:], self.found_agents_less_self))} on search_id={incoming_message.dialogue_reference[0]}.",
        )
        mock_own.assert_called_once()

        for agent in self.found_agents_less_self:
            mock_logger.assert_any_call(
                logging.INFO, f"sending CFP to agent={agent[-5:]}",
            )
            has_attributes, error_str = self.message_has_attributes(
                actual_message=self.get_message_from_outbox(),
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                to=agent,
                sender=self.self_address,
                query=self.cfp_query,
            )
            assert has_attributes, error_str

    def test_on_search_result_ii(self):
        """Test the _on_search_result method of the oef handler where number of agents found is 0."""
        # setup
        oef_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
            ),
        )
        oef_dialogue._is_seller_search = False
        search_for = "buyers"

        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                to=str(self.skill.skill_context.skill_id),
                agents=tuple(),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        # _handle_search
        mock_logger.assert_any_call(
            logging.INFO,
            f"found no {search_for} agents on search_id={incoming_message.dialogue_reference[0]}, continue searching.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            to=str(self.skill.skill_context.skill_id),
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


class TestContractApiHandler(BaseSkillTestCase):
    """Test contract_api handler of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.contract_api_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.logger = cls.contract_api_handler.context.logger

        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )

        cls.ledger_id = "some_ledger_id"
        cls.contract_id = "some_contract_id"
        cls.contract_address = "some_contract_address"
        cls.callable = "some_callable"
        cls.kwargs = Kwargs({"some_key": "some_value"})
        cls.body = {"some_key": "some_value"}
        cls.body_bytes = b"some_body"
        cls.nonce = "some_nonce"
        cls.counterprty_address = COUNTERPARTY_AGENT_ADDRESS
        cls.amount_by_currency_id = {"1": 50}
        cls.quantities_by_good_id = {"2": -10}
        cls.terms = Terms(
            cls.ledger_id,
            cls._skill.skill_context.agent_address,
            cls.counterprty_address,
            cls.amount_by_currency_id,
            cls.quantities_by_good_id,
            cls.nonce,
        )

        cls.list_of_contract_api_messages_get_deploy_tx = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": cls.ledger_id,
                    "contract_id": cls.contract_id,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )
        cls.list_of_contract_api_messages_raw_msg = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_RAW_MESSAGE,
                {
                    "ledger_id": cls.ledger_id,
                    "contract_id": cls.contract_id,
                    "contract_address": cls.contract_address,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )

        cls.cfp_query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                SUPPLY_DATAMODEL_NAME,
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )
        cls.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": cls.cfp_query}),
        )

    def test_setup(self):
        """Test the setup method of the contract_api handler."""
        assert self.contract_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=ContractApiMessage.Performative.STATE,
            state=State("some_ledger_id", {"some_key": "some_value"}),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid contract_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_raw_message(self):
        """Test the _handle_raw_message method of the signing handler."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:1],
            ),
        )
        fipa_dialogue.terms = self.terms

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages_raw_msg[:1],
            ),
        )
        contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=contract_api_dialogue,
                performative=ContractApiMessage.Performative.RAW_MESSAGE,
                raw_message=ContractApiMessage.RawMessage(
                    self.ledger_id, self.body_bytes
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received raw message={incoming_message}"
        )

        self.assert_quantity_in_decision_making_queue(1)
        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
            raw_message=RawMessage(
                self.ledger_id, self.body_bytes, is_deprecated_mode=True,
            ),
        )
        assert has_attributes, error_str

        assert (
            cast(
                SigningDialogue, self.signing_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the message to the decision maker. Waiting for confirmation ...",
        )

    def test_handle_raw_transaction(self):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:1],
            ),
        )
        fipa_dialogue.terms = self.terms

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages_get_deploy_tx[:1],
            ),
        )
        contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=contract_api_dialogue,
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=ContractApiMessage.RawTransaction(
                    self.ledger_id, self.body
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received raw transaction={incoming_message}"
        )

        self.assert_quantity_in_decision_making_queue(1)
        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
            raw_transaction=incoming_message.raw_transaction,
        )
        assert has_attributes, error_str

        assert (
            cast(
                SigningDialogue, self.signing_dialogues.get_dialogue(message)
            ).associated_fipa_dialogue
            == fipa_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        contract_api_dialogue = self.prepare_skill_dialogue(
            dialogues=self.contract_api_dialogues,
            messages=self.list_of_contract_api_messages_get_deploy_tx[:1],
        )
        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=contract_api_dialogue,
                performative=ContractApiMessage.Performative.ERROR,
                data=b"some_data",
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received contract_api error message={incoming_message} in dialogue={contract_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the signing handler."""
        # setup
        invalid_performative = ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id=self.ledger_id,
            contract_id=self.contract_id,
            callable=self.callable,
            kwargs=self.kwargs,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle contract_api message of performative={invalid_performative} in dialogue={self.contract_api_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the contract_api handler."""
        assert self.contract_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
