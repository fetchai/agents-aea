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

"""This module contains tests for decision_maker."""

from queue import Queue
from typing import Optional, cast
from unittest import mock

from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

import aea
import aea.decision_maker.gop
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.gop import DecisionMakerHandler
from aea.identity.base import Identity
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.signing.dialogues import SigningDialogue
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.fetchai.protocols.state_update.dialogues import StateUpdateDialogue
from packages.fetchai.protocols.state_update.dialogues import (
    StateUpdateDialogues as BaseStateUpdateDialogues,
)
from packages.fetchai.protocols.state_update.message import StateUpdateMessage

from tests.conftest import (
    COSMOS_PRIVATE_KEY_PATH,
    ETHEREUM_PRIVATE_KEY_PATH,
    FETCHAI_PRIVATE_KEY_PATH,
)
from tests.test_decision_maker.test_default import (
    BaseTestDecisionMaker as BaseTestDecisionMakerDefault,
)


class SigningDialogues(BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return SigningDialogue.Role.SKILL

        BaseSigningDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=SigningDialogue,
        )


class StateUpdateDialogues(BaseStateUpdateDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return StateUpdateDialogue.Role.DECISION_MAKER

        BaseStateUpdateDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


class TestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            aea.decision_maker.gop._default_logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup(cls):
        """Initialise the decision maker."""
        cls._patch_logger()
        cls.wallet = Wallet(
            {
                CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_PATH,
                EthereumCrypto.identifier: ETHEREUM_PRIVATE_KEY_PATH,
                FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_PATH,
            }
        )
        cls.agent_name = "test"
        cls.identity = Identity(
            cls.agent_name,
            addresses=cls.wallet.addresses,
            public_keys=cls.wallet.public_keys,
            default_address_key=FetchAICrypto.identifier,
        )
        cls.decision_maker_handler = DecisionMakerHandler(
            identity=cls.identity, wallet=cls.wallet, config={}
        )
        cls.decision_maker = DecisionMaker(cls.decision_maker_handler)

        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = FetchAICrypto.identifier

        cls.decision_maker.start()

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)

    def test_decision_maker_handle_state_update_initialize_and_apply(self):
        """Test the handle method for a stateUpdate message with Initialize and Apply performative."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_id": 20.0}
        exchange_params = {"FET": 10.0}
        currency_deltas = {"FET": -10}
        good_deltas = {"good_id": 1}

        state_update_dialogues = StateUpdateDialogues("agent")
        state_update_message_1 = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            dialogue_reference=state_update_dialogues.new_self_initiated_dialogue_reference(),
            amount_by_currency_id=currency_holdings,
            quantities_by_good_id=good_holdings,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
        )
        state_update_dialogue = cast(
            Optional[StateUpdateDialogue],
            state_update_dialogues.create_with_message(
                "decision_maker", state_update_message_1
            ),
        )
        assert state_update_dialogue is not None, "StateUpdateDialogue not created"
        self.decision_maker.handle(state_update_message_1)
        assert (
            self.decision_maker_handler.context.ownership_state.amount_by_currency_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.ownership_state.quantities_by_good_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.preferences.exchange_params_by_currency_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.preferences.utility_params_by_good_id
            is not None
        )

        state_update_message_2 = state_update_dialogue.reply(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=currency_deltas,
            quantities_by_good_id=good_deltas,
        )
        self.decision_maker.handle(state_update_message_2)
        expected_amount_by_currency_id = {
            key: currency_holdings.get(key, 0) + currency_deltas.get(key, 0)
            for key in set(currency_holdings) | set(currency_deltas)
        }
        expected_quantities_by_good_id = {
            key: good_holdings.get(key, 0) + good_deltas.get(key, 0)
            for key in set(good_holdings) | set(good_deltas)
        }
        assert (
            self.decision_maker_handler.context.ownership_state.amount_by_currency_id
            == expected_amount_by_currency_id
        ), "The amount_by_currency_id must be equal with the expected amount."
        assert (
            self.decision_maker_handler.context.ownership_state.quantities_by_good_id
            == expected_quantities_by_good_id
        )

    @classmethod
    def teardown(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.decision_maker.stop()


class TestDecisionMaker2(BaseTestDecisionMakerDefault):
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            aea.decision_maker.gop._default_logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup(cls):
        """Initialise the decision maker."""
        super().setup(
            decision_maker_handler_cls=DecisionMakerHandler,
            decision_maker_cls=DecisionMaker,
        )
        cls._patch_logger()

    @classmethod
    def teardown(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        super().teardown()
