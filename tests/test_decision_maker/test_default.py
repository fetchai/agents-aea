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

"""This module contains tests for decision_maker."""

import pytest
from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import ETHEREUM_PRIVATE_KEY_PATH
from aea_ledger_fetchai import FetchAICrypto
from aea_ledger_fetchai.test_tools.constants import (
    FETCHAI_PRIVATE_KEY_PATH,
    FETCHAI_TESTNET_CONFIG,
)

from aea.configurations.base import PublicId
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import DecisionMakerHandler
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedMessage,
    Terms,
)
from aea.identity.base import Identity
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.open_aea.protocols.signing.dialogues import SigningDialogue
from packages.open_aea.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.open_aea.protocols.signing.message import SigningMessage

from tests.conftest import (
    COSMOS_PRIVATE_KEY_PATH,
    MAX_FLAKY_RERUNS,
    get_wealth_if_needed,
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


class BaseTestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def setup(cls):
        """Initialise the decision maker."""
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
        cls.config = {}
        cls.decision_maker_handler = DecisionMakerHandler(
            identity=cls.identity, wallet=cls.wallet, config=cls.config
        )
        cls.decision_maker = DecisionMaker(cls.decision_maker_handler)

        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = FetchAICrypto.identifier

        cls.decision_maker.start()

    def test_decision_maker_config(self):
        """Test config property."""
        assert self.decision_maker_handler.config == self.config

    def test_decision_maker_execute_w_wrong_input(self):
        """Test the execute method with wrong input."""
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put_nowait("wrong input")
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put("wrong input")

    def test_decision_maker_queue_access_not_permitted(self):
        """Test the in queue of the decision maker can not be accessed."""
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.get()
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.get_nowait()
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.protected_get(
                access_code="some_invalid_code"
            )

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_handle_tx_signing_fetchai(self):
        """Test tx signing for fetchai."""
        fetchai_api = make_ledger_api(
            FetchAICrypto.identifier, **FETCHAI_TESTNET_CONFIG
        )
        sender_address = self.wallet.addresses["fetchai"]
        fc2 = make_crypto(FetchAICrypto.identifier)

        get_wealth_if_needed(sender_address, fetchai_api)

        amount = 10000
        transfer_transaction = fetchai_api.get_transfer_transaction(
            sender_address=sender_address,
            destination_address=fc2.address,
            amount=amount,
            tx_fee=1000,
            tx_nonce="something",
        )
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id=FetchAICrypto.identifier,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction(
                FetchAICrypto.identifier, transfer_transaction
            ),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_TRANSACTION
        )
        assert type(signing_msg_response.signed_transaction.body) == dict

    def test_handle_tx_signing_ethereum(self):
        """Test tx signing for ethereum."""
        tx = {"gasPrice": 30, "nonce": 1, "gas": 20000}
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction(EthereumCrypto.identifier, tx),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_TRANSACTION
        )
        assert type(signing_msg_response.signed_transaction.body) == dict

    def test_handle_tx_signing_unknown(self):
        """Test tx signing for unknown."""
        tx = {}
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction("unknown", tx),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert signing_msg_response.performative == SigningMessage.Performative.ERROR
        assert (
            signing_msg_response.error_code
            == SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING
        )

    def test_handle_message_signing_fetchai(self):
        """Test message signing for fetchai."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id=FetchAICrypto.identifier,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage(FetchAICrypto.identifier, message),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_MESSAGE
        )
        assert type(signing_msg_response.signed_message) == SignedMessage

    def test_handle_message_signing_ethereum(self):
        """Test message signing for ethereum."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage(EthereumCrypto.identifier, message),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_MESSAGE
        )
        assert type(signing_msg_response.signed_message) == SignedMessage

    def test_handle_message_signing_ethereum_deprecated(self):
        """Test message signing for ethereum deprecated."""
        message = b"0x11f3f9487724404e3a1fb7252a3226"
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage(
                EthereumCrypto.identifier, message, is_deprecated_mode=True
            ),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_MESSAGE
        )
        assert type(signing_msg_response.signed_message) == SignedMessage
        assert signing_msg_response.signed_message.is_deprecated_mode

    def test_handle_message_signing_unknown_and_two_dialogues(self):
        """Test message signing for unknown."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage("unknown", message),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        recovered_dialogue = signing_dialogues.update(signing_msg_response)
        assert recovered_dialogue is not None and recovered_dialogue == signing_dialogue
        assert signing_msg_response.performative == SigningMessage.Performative.ERROR
        assert (
            signing_msg_response.error_code
            == SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING
        )

    def test_handle_messages_from_two_dialogues_same_agent(self):
        """Test message signing for unknown."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        dialogue_reference = signing_dialogues.new_self_initiated_dialogue_reference()
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=dialogue_reference,
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage("unknown", message),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert signing_msg_response is not None
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=dialogue_reference,
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage("unknown", message),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        with pytest.raises(Exception):
            # Exception occurs because the same counterparty sends two identical dialogue references
            self.decision_maker.message_out_queue.get(timeout=1)
        # test twice; should work again even from same agent
        signing_dialogues = SigningDialogues(
            str(PublicId("author", "a_skill", "0.1.0"))
        )
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage("unknown", message),
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        assert signing_dialogue is not None
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert signing_msg_response is not None

    @classmethod
    def teardown(cls):
        """Tear the tests down."""
        cls.decision_maker.stop()


class TestDecisionMaker(BaseTestDecisionMaker):
    """Run test for default decision maker."""
