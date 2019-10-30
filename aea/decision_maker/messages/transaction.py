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
from typing import Dict, Optional, Union, cast

from aea.protocols.base import Message

TransactionId = str
Address = str


class TransactionMessage(Message):
    """The transaction message class."""

    class Performative(Enum):
        """Transaction performative."""

        PROPOSE = "propose"
        ACCEPT = "accept"
        REJECT = "reject"

    def __init__(self, performative: Union[str, Performative],
                 skill_id: str,
                 transaction_id: TransactionId,
                 sender: Address,
                 counterparty: Address,
                 is_sender_buyer: bool,
                 currency_pbk: str,
                 amount: int,
                 sender_tx_fee: int,
                 counterparty_tx_fee: int,
                 quantities_by_good_pbk: Dict[str, int],
                 transaction_digest: Optional[str] = None,
                 dialogue_label: Optional[Dict[str, str]] = None,
                 ledger_id: Optional[str] = None,
                 **kwargs):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param skill_id: the skill sending the transaction message
        :param transaction_id: the id of the transaction.
        :param sender: the sender of the transaction.
        :param counterparty: the counterparty of the transaction.
        :param is_sender_buyer: whether the transaction is sent by a buyer.
        :param currency_pbk: the currency of the transaction.
        :param sender_tx_fee: the part of the tx fee paid by the sender
        :param counterparty_tx_fee: the part of the tx fee paid by the counterparty
        :param amount: the amount of money involved.
        :param quantities_by_good_pbk: a map from good pbk to the quantity of that good involved in the transaction.
        :param transaction_digest: the transaction digest
        :param dialog_label: the dialog label
        """
        super().__init__(performative=performative,
                         skill_id=skill_id,
                         transaction_id=transaction_id,
                         sender=sender,
                         counterparty=counterparty,
                         is_sender_buyer=is_sender_buyer,
                         currency_pbk=currency_pbk,
                         sender_tx_fee=sender_tx_fee,
                         counterparty_tx_fee=counterparty_tx_fee,
                         amount=amount,
                         quantities_by_good_pbk=quantities_by_good_pbk,
                         transaction_digest=transaction_digest,
                         dialogue_label=dialogue_label,
                         ledger_id=ledger_id,
                         **kwargs)
        assert self.check_consistency(), "Transaction message initialization inconsistent."

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert self.is_set("performative")
            assert self.is_set("skill_id")
            assert self.is_set("transaction_id")
            assert self.is_set("sender")
            assert self.is_set("counterparty")
            sender = self.get("sender")
            counterparty = self.get("counterparty")
            assert sender != counterparty
            assert self.is_set("is_sender_buyer")
            assert self.is_set("currency_pbk")
            assert self.is_set("amount")
            amount = self.get("amount")
            amount = cast(int, amount)
            assert amount >= 0
            assert self.is_set("sender_tx_fee")
            sender_tx_fee = self.get("sender_tx_fee")
            sender_tx_fee = cast(int, sender_tx_fee)
            assert sender_tx_fee >= 0
            assert self.is_set("counterparty_tx_fee")
            counterparty_tx_fee = self.get("counterparty_tx_fee")
            counterparty_tx_fee = cast(int, counterparty_tx_fee)
            assert counterparty_tx_fee >= 0
            assert self.is_set("quantities_by_good_pbk")
            quantities_by_good_pbk = self.get("quantities_by_good_pbk")
            quantities_by_good_pbk = cast(Dict[str, int], quantities_by_good_pbk)
            assert len(quantities_by_good_pbk.keys()) == len(set(quantities_by_good_pbk.keys()))
            assert all(quantity >= 0 for quantity in quantities_by_good_pbk.values())
            assert self.is_set("transaction_digest")
            assert self.is_set("dialogue_label")
            assert self.is_set("ledger_id")
        except (AssertionError, KeyError):
            return False
        return True

    def matches(self, other: 'TransactionMessage') -> bool:
        """
        Check if the transaction matches with another (mirroring) transaction.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, TransactionMessage) \
            and self.get("performative") == other.get("performative") \
            and self.get("skill_id") == other.get("skill_id") \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("counterparty") \
            and self.get("counterparty") == other.get("sender") \
            and self.get("is_sender_buyer") != other.get("is_sender_buyer") \
            and self.get("currency") == other.get("currency") \
            and self.get("amount") == other.get("amount") \
            and self.get("sender_tx_fee") == other.get("counterparty_tx_fee") \
            and self.get("counterparty_tx_fee") == other.get("sender_tx_fee") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk") \
            and self.get("transaction_digest") == other.get("transaction_digest") \
            and self.get("dialogue_label") == other.get("dialogue_label") \
            and self.get("ledger_id") == other.get("ledger_id")

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
                                    skill_id=cast(str, other.get("skill_id")),
                                    transaction_id=cast(str, other.get("transaction_id")),
                                    sender=cast(Address, other.get("sender")),
                                    counterparty=cast(Address, other.get("counterparty")),
                                    is_sender_buyer=cast(bool, other.get("is_sender_buyer")),
                                    currency_pbk=cast(str, other.get("currency_pbk")),
                                    sender_tx_fee=cast(int, other.get("sender_tx_fee")),
                                    counterparty_tx_fee=cast(int, other.get("counterparty_tx_fee")),
                                    amount=cast(int, other.get("amount")),
                                    quantities_by_good_pbk=cast(Dict[str, int], other.get("quantities_by_good_pbk")),
                                    transaction_digest=transaction_digest,
                                    dialogue_label=cast(Dict, other.get("dialogue_label")),
                                    ledger_id=other.get("ledger_id"))
        return tx_msg

    def __eq__(self, other: object) -> bool:
        """
        Compare to another object.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, TransactionMessage) \
            and self.get("performative") == other.get("performative") \
            and self.get("skill_id") == other.get("skill_id") \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("sender") \
            and self.get("counterparty") == other.get("counterparty") \
            and self.get("is_sender_buyer") == other.get("is_sender_buyer") \
            and self.get("currency") == other.get("currency") \
            and self.get("amount") == other.get("amount") \
            and self.get("sender_tx_fee") == other.get("sender_tx_fee") \
            and self.get("counterparty_tx_fee") == other.get("counterparty_tx_fee") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk") \
            and self.get("transaction_digest") == other.get("transaction_digest") \
            and self.get("dialogue_label") == other.get("dialogue_label")\
            and self.get("ledger_id") == other.get("ledger_id")
