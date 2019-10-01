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


from aea.protocols.base import Message

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
            assert amount >= 0
            assert self.is_set("quantities_by_good_pbk")
            quantities_by_good_pbk = self.get("quantities_by_good_pbk")
            assert len(quantities_by_good_pbk.keys()) == len(set(quantities_by_good_pbk.keys()))
            assert all(quantity >= 0 for quantity in quantities_by_good_pbk.values())
        except (AssertionError, KeyError):
            return False
        return True

    # def to_dict(self) -> Dict[str, Any]:
    #     """From object to dictionary."""
    #     return {
    #         "transaction_id": self.transaction_id,
    #         "is_sender_buyer": self.is_sender_buyer,
    #         "counterparty": self.counterparty,
    #         "amount": self.amount,
    #         "quantities_by_good_pbk": self.quantities_by_good_pbk,
    #         "sender": self.sender
    #     }

    # @classmethod
    # def from_dict(cls, d: Dict[str, Any]) -> 'Transaction':
    #     """Return a class instance from a dictionary."""
    #     return cls(
    #         transaction_id=d["transaction_id"],
    #         is_sender_buyer=d["is_sender_buyer"],
    #         counterparty=d["counterparty"],
    #         amount=d["amount"],
    #         quantities_by_good_pbk=d["quantities_by_good_pbk"],
    #         sender=d["sender"]
    #     )

    # @classmethod
    # def from_proposal(cls, proposal: Description, transaction_id: TransactionId,
    #                   is_sender_buyer: bool, counterparty: Address, sender: Address) -> 'Transaction':
    #     """
    #     Create a transaction from a proposal.

    #     :param proposal: the proposal
    #     :param transaction_id: the transaction id
    #     :param is_sender_buyer: whether the sender is the buyer
    #     :param counterparty: the counterparty public key
    #     :param sender: the sender public key
    #     :return: Transaction
    #     """
    #     data = copy.deepcopy(proposal.values)
    #     price = data.pop("price")
    #     quantity_by_good_pbk = {key: value for key, value in data.items()}
    #     return Transaction(transaction_id, is_sender_buyer, counterparty, price, quantity_by_good_pbk, sender)

    # @classmethod
    # def from_message(cls, message: TACMessage, sender: Address) -> 'Transaction':
    #     """
    #     Create a transaction from a proposal.

    #     :param message: the message
    #     :return: Transaction
    #     """
    #     return Transaction(message.get("transaction_id"), message.get("is_sender_buyer"), message.get("counterparty"), message.get("amount"), message.get("quantities_by_good_pbk"), sender)

    def matches(self, other: 'TransactionMessage') -> bool:
        """
        Check if the transaction matches with another (mirroring) transaction.

        :param other: the other transaction to match.
        :return: True if the two
        """
        result = True
        result = result and self.get("transaction_id") == other.get("transaction_id")
        result = result and self.get("sender") == other.get("counterparty")
        result = result and self.get("counterparty") == other.get("sender")
        result = result and self.get("is_sender_buyer") != other.get("is_sender_buyer")
        result = result and self.get("amount") == other.get("amount")
        result = result and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk")

        return result

    def __eq__(self, other: 'TransactionMessage') -> bool:
        """
        Compare to another object.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return isinstance(other, TransactionManager) \
            and self.get("transaction_id") == other.get("transaction_id") \
            and self.get("sender") == other.get("sender") \
            and self.get("counterparty") == other.get("counterparty") \
            and self.get("is_sender_buyer") == other.get("is_sender_buyer") \
            and self.get("amount") == other.get("amount") \
            and self.get("quantities_by_good_pbk") == other.get("quantities_by_good_pbk") \
