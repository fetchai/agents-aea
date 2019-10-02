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

from typing import Dict, cast

from aea.protocols.base import Message

TransactionId = str
Address = str


class TransactionMessage(Message):
    """The transaction message class."""

    def __init__(self, transaction_id: TransactionId,
                 sender: Address,
                 counterparty: Address,
                 is_sender_buyer: bool,
                 amount: float,
                 quantities_by_good_pbk: Dict[str, int],
                 **kwargs):
        """
        Instantiate transaction message.

        :param transaction_id: the id of the transaction.
        :param is_sender_buyer: whether the transaction is sent by a buyer.
        :param counterparty: the counterparty of the transaction.
        :param amount: the amount of money involved.
        :param quantities_by_good_pbk: a map from good pbk to the quantity of that good involved in the transaction.
        :param sender: the sender of the transaction.
        """
        super().__init__(transaction_id=transaction_id,
                         sender=sender,
                         counterparty=counterparty,
                         is_sender_buyer=is_sender_buyer,
                         amount=amount,
                         quantities_by_good_pbk=quantities_by_good_pbk,
                         **kwargs)
        assert self.check_consistency(), "FIPAMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert self.is_set("transaction_id")
            assert self.is_set("sender")
            assert self.is_set("counterparty")
            sender = self.get("sender")
            counterparty = self.get("counterparty")
            assert sender != counterparty
            assert self.is_set("is_sender_buyer")
            assert self.is_set("amount")
            amount = self.get("amount")
            cast(float, amount)
            assert amount >= 0.0
            assert self.is_set("quantities_by_good_pbk")
            quantities_by_good_pbk = self.get("quantities_by_good_pbk")
            cast(Dict[str, int], quantities_by_good_pbk)
            assert len(quantities_by_good_pbk.keys()) == len(set(quantities_by_good_pbk.keys()))
            assert all(quantity >= 0 for quantity in quantities_by_good_pbk.values())
        except (AssertionError, KeyError):
            return False
        return True

    def matches(self, other: 'TransactionMessage') -> bool:
        """
        Check if the transaction matches with another (mirroring) transaction.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, 'TransactionMessage') \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("counterparty") \
            and self.get("counterparty") == other.get("sender") \
            and self.get("is_sender_buyer") != other.get("is_sender_buyer") \
            and self.get("amount") == other.get("amount") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk")

    def __eq__(self, other: 'TransactionMessage') -> bool:
        """
        Compare to another object.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, 'TransactionMessage') \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("sender") \
            and self.get("counterparty") == other.get("counterparty") \
            and self.get("is_sender_buyer") == other.get("is_sender_buyer") \
            and self.get("amount") == other.get("amount") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk")
