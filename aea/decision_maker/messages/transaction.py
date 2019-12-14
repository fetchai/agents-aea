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

"""The transaction message module."""

from enum import Enum
from typing import Any, Dict, List, Optional, cast

from aea.crypto.ledger_apis import SUPPORTED_LEDGER_APIS
from aea.decision_maker.messages.base import InternalMessage
from aea.configurations.base import Address

TransactionId = str
OFF_CHAIN = 'off_chain'
SUPPORTED_LEDGER_IDS = SUPPORTED_LEDGER_APIS + [OFF_CHAIN]


class TransactionMessage(InternalMessage):
    """The transaction message class."""

    class Performative(Enum):
        """Transaction performative."""

        PROPOSE = "propose"
        SIGN = "sign"
        ACCEPT = "accept"
        REJECT = "reject"

    def __init__(self, performative: Performative,
                 skill_ids: List[str],
                 transaction_id: TransactionId,
                 sender: Address,
                 counterparty: Address,
                 is_sender_buyer: bool,
                 currency_pbk: str,
                 amount: int,
                 sender_tx_fee: int,
                 counterparty_tx_fee: int,
                 ledger_id: str,
                 info: Dict[str, Any],
                 quantities_by_good_pbk: Dict[str, int],
                 **kwargs):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param skill_ids: the skills to receive the transaction message response
        :param transaction_id: the id of the transaction.
        :param sender: the sender of the transaction.
        :param counterparty: the counterparty of the transaction.
        :param is_sender_buyer: whether the transaction is sent by a buyer.
        :param currency_pbk: the currency of the transaction.
        :param sender_tx_fee: the part of the tx fee paid by the sender
        :param counterparty_tx_fee: the part of the tx fee paid by the counterparty
        :param amount: the amount of money involved.
        :param ledger_id: the ledger id
        :param info: a dictionary for arbitrary information
        :param quantities_by_good_pbk: a map from good pbk to the quantity of that good involved in the transaction.
        """
        super().__init__(performative=performative,
                         skill_ids=skill_ids,
                         transaction_id=transaction_id,
                         sender=sender,
                         counterparty=counterparty,
                         is_sender_buyer=is_sender_buyer,
                         currency_pbk=currency_pbk,
                         sender_tx_fee=sender_tx_fee,
                         counterparty_tx_fee=counterparty_tx_fee,
                         amount=amount,
                         ledger_id=ledger_id,
                         info=info,
                         quantities_by_good_pbk=quantities_by_good_pbk,
                         **kwargs)
        assert self.check_consistency(), "Transaction message initialization inconsistent."

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "Performative is not set."
        return TransactionMessage.Performative(self.get('performative'))

    @property
    def skill_ids(self) -> List[str]:
        """Get the list of skill_id from the message."""
        assert self.is_set("skill_ids"), "Skill_ids is not set."
        return cast(List[str], self.get("skill_ids"))

    @property
    def transaction_id(self) -> str:
        """Get the transaction_id from the message."""
        assert self.is_set("transaction_id"), "Transaction_id is not set."
        return cast(str, self.get("transaction_id"))

    @property
    def sender(self) -> Address:
        """Get the address of the sender."""
        assert self.is_set("sender"), "Sender is not set."
        return cast(Address, self.get("sender"))

    @property
    def counterparty(self) -> Address:
        """Get the counterparty of the message."""
        assert self.is_set("counterparty"), "Counterparty is not set."
        return cast(Address, self.get("counterparty"))

    @property
    def is_sender_buyer(self) -> bool:
        """Get if the sender is buyer."""
        assert self.is_set("is_sender_buyer"), "Is_sender_buyer is not set."
        return cast(bool, self.get("is_sender_buyer"))

    @property
    def currency_pbk(self) -> str:
        """Get the currency pbk."""
        assert self.is_set("currency_pbk"), "Currency_pbk is not set."
        return cast(str, self.get("currency_pbk"))

    @property
    def amount(self) -> int:
        """Get the amount from the message."""
        assert self.is_set("amount"), "Amount is not set."
        return cast(int, self.get("amount"))

    @property
    def sender_tx_fee(self) -> int:
        """Get the fee for the sender from the messgae."""
        assert self.is_set("sender_tx_fee"), "Sender_tx_fee is not set."
        return cast(int, self.get("sender_tx_fee"))

    @property
    def counterparty_tx_fee(self) -> int:
        """Get the fee for the counterparty from the messgae."""
        assert self.is_set("counterparty_tx_fee"), "counterparty_tx_fee is not set."
        return cast(int, self.get("counterparty_tx_fee"))

    @property
    def ledger_id(self) -> str:
        """Get the ledger_id."""
        assert self.is_set("ledger_id"), "Ledger_id is not set."
        return cast(str, self.get("ledger_id"))

    @property
    def info(self) -> Dict[str, Any]:
        """Get the infos from the message."""
        assert self.is_set("info"), "Info is not set."
        return cast(Dict[str, Any], self.get("info"))

    @property
    def quantities_by_good_pbk(self) -> Dict[str, int]:
        """Get he quantities by good public keys."""
        assert self.is_set("quantities_by_good_pbk"), "quantities_by_good_pbk is not set."
        return cast(Dict[str, int], self.get("quantities_by_good_pbk"))

    @property
    def transaction_digest(self) -> Optional[str]:
        """Get the transaction digest."""
        assert self.is_set("transaction_digest"), "Transaction digest is not set."
        return cast(Optional[str], self.get("transaction_digest"))

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert isinstance(self.performative, TransactionMessage.Performative), "Performative is not of correct type."
            assert isinstance(self.skill_ids, list), "Skill_ids must be of type list."
            assert isinstance(self.transaction_id, str), "Transaction_id must of type str."
            assert isinstance(self.sender, Address), "Sender must be of type address."
            assert isinstance(self.counterparty, Address), "Counterparty must be of type address"
            assert self.sender != self.counterparty, "Sender must be different of counterparty."
            assert isinstance(self.is_sender_buyer, bool), "Is_sender_buyer must be of type bool."
            assert isinstance(self.currency_pbk, str), "Currency_pbk must be of type str."
            assert isinstance(self.amount, int), "Amount must be of type int"
            assert self.amount >= 0, "Amount must be more than zero."
            assert isinstance(self.sender_tx_fee, int), "Sender_tx_fee must be of type int."
            assert self.sender_tx_fee >= 0, "Sender transaction fee must be greater or equal to zero."
            assert isinstance(self.counterparty_tx_fee, int), "Counter_tx_fee must be of type int."
            assert self.counterparty_tx_fee >= 0, "Counterparty transaction fee must be greater or equal to zero."
            assert isinstance(self.ledger_id, str) and self.ledger_id in SUPPORTED_LEDGER_IDS, "Ledger_id must be str and " \
                                                                                               "must in the supported ledger ids."

            if self.performative == self.Performative.PROPOSE or self.performative == self.Performative.SIGN:
                assert isinstance(self.info, dict)
                for key, value in self.info.items():
                    assert isinstance(key, str)
                assert type(self.quantities_by_good_pbk) == dict
                for key, value in self.quantities_by_good_pbk.items():
                    assert isinstance(key, str)
                    assert isinstance(value, int)
                assert len(self.quantities_by_good_pbk.keys()) == len(set(self.quantities_by_good_pbk.keys()))
                assert all(quantity >= 0 for quantity in self.quantities_by_good_pbk.values())
                assert len(self.body) == 13
            elif self.performative == self.Performative.ACCEPT or self.performative == self.Performative.REJECT:
                assert self.transaction_digest is None or isinstance(self.transaction_digest, str)
                assert len(self.body) == 14
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, KeyError):
            return False
        return True

    @classmethod
    def respond_with(cls, other: 'TransactionMessage', performative: Performative, transaction_digest: Optional[str] = None) -> 'TransactionMessage':
        """
        Create response message.

        :param other: TransactionMessage
        :param performative: the performative
        :param transaction_digest: the transaction digest
        :return: a transaction message object
        """
        tx_msg = TransactionMessage(performative=performative,
                                    skill_ids=other.skill_ids,
                                    transaction_id=other.transaction_id,
                                    sender=other.sender,
                                    counterparty=other.counterparty,
                                    is_sender_buyer=other.is_sender_buyer,
                                    currency_pbk=other.currency_pbk,
                                    sender_tx_fee=other.sender_tx_fee,
                                    counterparty_tx_fee=other.counterparty_tx_fee,
                                    amount=other.amount,
                                    ledger_id=other.ledger_id,
                                    info=other.info,
                                    quantities_by_good_pbk=other.quantities_by_good_pbk,
                                    transaction_digest=transaction_digest)
        return tx_msg
