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
"""This module contains the tests of the handler classes of the ml_train skill."""
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import cast
from unittest.mock import patch

import numpy as np
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
from aea.skills.tasks import TaskManager
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.ml_data_provider.strategy import (
    Strategy as DataProviderStrategy,
)
from packages.fetchai.skills.ml_train.behaviours import TransactionBehaviour
from packages.fetchai.skills.ml_train.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.ml_train.handlers import (
    DUMMY_DIGEST,
    LEDGER_API_ADDRESS,
    LedgerApiHandler,
    MlTradeHandler,
    OEFSearchHandler,
    SigningHandler,
)
from packages.fetchai.skills.ml_train.strategy import Strategy

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_ml_train.helpers import produce_data


class TestMlTradeHandler(BaseSkillTestCase):
    """Test ml_trade handler of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ml_handler = cast(
            MlTradeHandler, cls._skill.skill_context.handlers.ml_trade
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.tx_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.ledger_api_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.task_manager = cast(TaskManager, cls._skill.skill_context.task_manager)

        cls.logger = cls._skill.skill_context.logger

        cls.batch_size = 32
        cls.price_per_data_batch = 10
        cls.seller_tx_fee = 0
        cls.buyer_tx_fee = 0
        cls.currency_id = "FET"
        cls.ledger_id = "FET"
        cls.service_id = "data_service"

        cls.terms = Description(
            {
                "batch_size": cls.batch_size,
                "price": cls.price_per_data_batch,
                "seller_tx_fee": cls.seller_tx_fee,
                "buyer_tx_fee": cls.buyer_tx_fee,
                "currency_id": cls.currency_id,
                "ledger_id": cls.ledger_id,
                "address": cls._skill.skill_context.agent_address,
                "service_id": cls.service_id,
                "nonce": uuid.uuid4().hex,
            }
        )

        cls.list_of_messages = (
            DialogueMessage(MlTradeMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(MlTradeMessage.Performative.TERMS, {"terms": cls.terms}),
            DialogueMessage(
                MlTradeMessage.Performative.ACCEPT,
                {"terms": cls.terms, "tx_digest": "some_tx_digest"},
            ),
        )

    def test_setup(self):
        """Test the setup method of the ml_trade handler."""
        assert self.ml_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the ml_trade handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=MlTradeMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=MlTradeMessage.Performative.ACCEPT,
            terms=self.terms,
            tx_digest="some_tx_digest",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ml_trade message={incoming_message}, unidentified dialogue.",
        )

        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"ml_trade_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_terms_not_affordable_nor_acceptable(self):
        """Test the _handle_propose method of the ml_trade handler where terms is not affordable nor acceptable."""
        # setup
        ml_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ml_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.TERMS,
            terms=self.terms,
        )

        # operation
        with patch.object(
            self.strategy, "is_acceptable_terms", return_value=False,
        ) as mocked_acceptable:
            with patch.object(
                self.strategy, "is_affordable_terms", return_value=False,
            ) as mocked_affordable:
                with patch.object(self.logger, "log") as mock_logger:
                    self.ml_handler.handle(incoming_message)

        # after
        incoming_message = cast(MlTradeMessage, incoming_message)
        mock_logger.assert_any_call(
            logging.INFO,
            f"received terms message from {incoming_message.sender[-5:]}: terms={incoming_message.terms.values}",
        )

        mocked_acceptable.assert_called_once()
        mocked_affordable.assert_called_once()

        mock_logger.assert_any_call(
            logging.INFO, "rejecting, terms are not acceptable and/or affordable",
        )

        self.assert_quantity_in_outbox(0)

    def test_handle_terms_is_affordable_and_acceptable_not_ledger(self):
        """Test the _handle_terms method of the ml_train handler where terms is affordable and acceptable and is NOT ledger_tx."""
        # setup
        self.strategy._is_ledger_tx = False
        ml_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ml_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.TERMS,
            terms=self.terms,
        )

        # operation
        with patch.object(
            self.strategy, "is_acceptable_terms", return_value=True,
        ) as mocked_acceptable:
            with patch.object(
                self.strategy, "is_affordable_terms", return_value=True,
            ) as mocked_affordable:
                with patch.object(self.logger, "log") as mock_logger:
                    self.ml_handler.handle(incoming_message)

        # after
        incoming_message = cast(MlTradeMessage, incoming_message)
        mock_logger.assert_any_call(
            logging.INFO,
            f"received terms message from {incoming_message.sender[-5:]}: terms={incoming_message.terms.values}",
        )

        mocked_acceptable.assert_called_once()
        mocked_affordable.assert_called_once()

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=MlTradeMessage,
            performative=MlTradeMessage.Performative.ACCEPT,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            tx_digest=DUMMY_DIGEST,
            terms=self.terms,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, "sending dummy transaction digest ...",
        )

    def test_handle_terms_is_affordable_and_acceptable_is_ledger(self):
        """Test the _handle_terms method of the ml_train handler where terms is affordable and acceptable and IS ledger_tx."""
        # setup
        self.strategy._is_ledger_tx = True
        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues, messages=self.list_of_messages[:1],
            ),
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.TERMS,
            terms=self.terms,
        )
        mocked_terms_from_proposal = "some_terms"

        # operation
        with patch.object(
            self.strategy, "is_acceptable_terms", return_value=True,
        ) as mocked_acceptable:
            with patch.object(
                self.strategy, "is_affordable_terms", return_value=True,
            ) as mocked_affordable:
                with patch.object(
                    self.strategy,
                    "terms_from_proposal",
                    return_value=mocked_terms_from_proposal,
                ) as mocked_terms_from:
                    with patch.object(self.logger, "log") as mock_logger:
                        self.ml_handler.handle(incoming_message)

        # after
        incoming_message = cast(MlTradeMessage, incoming_message)
        mock_logger.assert_any_call(
            logging.INFO,
            f"received terms message from {incoming_message.sender[-5:]}: terms={incoming_message.terms.values}",
        )

        mocked_acceptable.assert_called_once()
        mocked_affordable.assert_called_once()
        mocked_terms_from.assert_called_with(self.terms)

        assert ml_dialogue.terms == mocked_terms_from_proposal
        assert ml_dialogue in self.tx_behaviour.waiting

    @pytest.mark.skipif(
        sys.version_info >= (3, 9),
        reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
    )
    def test_handle_data_with_data(self):
        """Test the _handle_data method of the ml_trade handler where data is NOT None."""
        # setup
        data = produce_data(self.batch_size)
        payload = DataProviderStrategy.encode_sample_data(data)

        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues, messages=self.list_of_messages[:3],
            ),
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.DATA,
            terms=self.terms,
            payload=payload,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received data message from {COUNTERPARTY_AGENT_ADDRESS[-5:]}: data shape={data[0].shape}, terms={self.terms.values}",
        )
        assert len(self.strategy.data[0]) == len(data)
        assert np.array_equal(self.strategy.data[0][0], data[0]) is True
        assert np.array_equal(self.strategy.data[0][1], data[1]) is True
        assert self.strategy.is_searching is True

    def test_handle_data_without_data(self):
        """Test the _handle_data method of the ml_trade handler where data IS None."""
        # setup
        data = None
        payload = json.dumps(data).encode("utf-8")

        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues, messages=self.list_of_messages[:3],
            ),
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.DATA,
            terms=self.terms,
            payload=payload,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received data message with no data from {COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the ml_trade handler."""
        # setup
        ml_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ml_dialogues, messages=self.list_of_messages[:2],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.ACCEPT,
            terms=self.terms,
            tx_digest="some_tx_digest",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ml_trade message of performative={incoming_message.performative} in dialogue={ml_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the ml handler."""
        assert self.ml_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            OEFSearchHandler, cls._skill.skill_context.handlers.oef_search
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.logger = cls._skill.skill_context.logger
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
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
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
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
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
        """Test the _handle_search method of the oef_search handler where len(agent)<max_negotiations."""
        # setup
        self.strategy._max_negotiations = 3
        self.strategy._is_searching = True

        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
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
                message_type=MlTradeMessage,
                performative=MlTradeMessage.Performative.CFP,
                to=agent,
                sender=self.skill.skill_context.agent_address,
                target=0,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            mock_logger.assert_any_call(logging.INFO, f"sending CFT to agent={agent}")

    def test_handle_search_ii(self):
        """Test the _handle_search method of the oef_search handler where number of agents founds is 0."""
        # setup
        self.strategy._max_negotiations = 1
        self.strategy._is_searching = True

        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        agents = ()
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=agents,
            agents_info=OefSearchMessage.AgentsInfo({}),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"found no agents in dialogue={oef_dialogue}, continue searching.",
        )
        assert self.strategy.is_searching is True
        self.assert_quantity_in_outbox(0)

    def test_handle_search_more_than_max_negotiation(self):
        """Test the _handle_search method of the oef_search handler where number of agents is more than max_negotiation."""
        # setup
        self.strategy._max_negotiations = 1
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
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
                message_type=MlTradeMessage,
                performative=MlTradeMessage.Performative.CFP,
                to=agents[idx],
                sender=self.skill.skill_context.agent_address,
                target=0,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            mock_logger.assert_any_call(
                logging.INFO, f"sending CFT to agent={agents[idx]}"
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


class TestSigningHandler(BaseSkillTestCase):
    """Test signing handler of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.tx_terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )

        cls.batch_size = 32
        cls.price_per_data_batch = 10
        cls.seller_tx_fee = 0
        cls.buyer_tx_fee = 0
        cls.currency_id = "FET"
        cls.ledger_id = "FET"
        cls.service_id = "data_service"

        cls.terms = Description(
            {
                "batch_size": cls.batch_size,
                "price": cls.price_per_data_batch,
                "seller_tx_fee": cls.seller_tx_fee,
                "buyer_tx_fee": cls.buyer_tx_fee,
                "currency_id": cls.currency_id,
                "ledger_id": cls.ledger_id,
                "address": cls._skill.skill_context.agent_address,
                "service_id": cls.service_id,
                "nonce": uuid.uuid4().hex,
            }
        )

        cls.list_of_messages = (
            DialogueMessage(MlTradeMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(MlTradeMessage.Performative.TERMS, {"terms": cls.terms}),
            DialogueMessage(
                MlTradeMessage.Performative.ACCEPT,
                {"terms": cls.terms, "tx_digest": "some_tx_digest"},
            ),
        )

        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": cls.tx_terms,
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

    def test_handle_signed_transaction_last_ledger_api_message_is_none(self,):
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

    def test_handle_signed_transaction_last_ledger_api_message_is_not_none(self,):
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
        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues,
                messages=self.list_of_messages[:3],
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
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue

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
            TransactionBehaviour, self.skill.skill_context.behaviours.transaction
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
            terms=self.tx_terms,
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


class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.transaction_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )

        cls.tx_terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )

        cls.batch_size = 32
        cls.price_per_data_batch = 10
        cls.seller_tx_fee = 0
        cls.buyer_tx_fee = 0
        cls.currency_id = "FET"
        cls.ledger_id = "FET"
        cls.service_id = "data_service"

        cls.terms = Description(
            {
                "batch_size": cls.batch_size,
                "price": cls.price_per_data_batch,
                "seller_tx_fee": cls.seller_tx_fee,
                "buyer_tx_fee": cls.buyer_tx_fee,
                "currency_id": cls.currency_id,
                "ledger_id": cls.ledger_id,
                "address": cls._skill.skill_context.agent_address,
                "service_id": cls.service_id,
                "nonce": uuid.uuid4().hex,
            }
        )

        cls.list_of_messages = (
            DialogueMessage(MlTradeMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(MlTradeMessage.Performative.TERMS, {"terms": cls.terms}),
            DialogueMessage(
                MlTradeMessage.Performative.ACCEPT,
                {"terms": cls.terms, "tx_digest": "some_tx_digest"},
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
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                {"terms": cls.tx_terms},
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
            f"you have no starting balance on {self.strategy.ledger_id} ledger!",
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
        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues,
                messages=self.list_of_messages[:3],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue
        ml_dialogue.terms = self.tx_terms
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
            terms=self.tx_terms,
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
            logging.INFO, "checking transaction is settled.",
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
        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues,
                messages=self.list_of_messages[:3],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue
        ml_dialogue.terms = self.tx_terms
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
            f"informing counterparty={ml_dialogue.dialogue_label.dialogue_opponent_addr[-5:]} of transaction digest={self.transaction_digest}.",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=MlTradeMessage,
            performative=MlTradeMessage.Performative.ACCEPT,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            tx_digest=self.transaction_digest.body,
            terms=self.terms,
        )
        assert has_attributes, error_str

    def test_handle_transaction_receipt_ii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where ml dialogue's last_incoming_message is None."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues,
                messages=self.list_of_messages[:3],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue

        ml_dialogue._incoming_messages = []

        ml_dialogue.terms = self.tx_terms
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
                        ValueError, match="Could not retrieve last ml_trade message"
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
        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues,
                messages=self.list_of_messages[:3],
                is_agent_to_agent_messages=True,
            ),
        )
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue
        ml_dialogue.terms = self.tx_terms
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
        ledger_api_dialogue.associated_ml_trade_dialogue = "mock"
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
