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

from aea.crypto.ledger_apis import SUPPORTED_CURRENCIES, SUPPORTED_LEDGER_APIS
from aea.decision_maker.messages.base import InternalMessage
from aea.mail.base import Address

TransactionId = str
LedgerId = str
OFF_CHAIN = "off_chain"
SUPPORTED_LEDGER_IDS = SUPPORTED_LEDGER_APIS + [OFF_CHAIN]


class TransactionMessage(InternalMessage):
    """The transaction message class."""

    class Performative(Enum):
        """Transaction performative."""

        PROPOSE_FOR_SETTLEMENT = "propose_for_settlement"
        SUCCESSFUL_SETTLEMENT = "successful_settlement"
        FAILED_SETTLEMENT = "failed_settlement"
        REJECTED_SETTLEMENT = "rejected_settlement"
        PROPOSE_FOR_SIGNING = "propose_for_signing"
        SUCCESSFUL_SIGNING = "successful_signing"
        REJECTED_SIGNING = "rejected_signing"

    def __init__(
        self,
        performative: Performative,
        skill_callback_ids: List[str],
        tx_id: TransactionId,
        tx_sender_addr: Address,
        tx_counterparty_addr: Address,
        tx_amount_by_currency_id: Dict[str, int],
        tx_sender_fee: int,
        tx_counterparty_fee: int,
        tx_quantities_by_good_id: Dict[str, int],
        ledger_id: LedgerId,
        info: Dict[str, Any],
        **kwargs
    ):
        """
        Instantiate transaction message.

        :param performative: the performative
        :param skill_callback_ids: the skills to receive the transaction message response
        :param tx_id: the id of the transaction.
        :param tx_sender: the sender of the transaction.
        :param tx_counterparty: the counterparty of the transaction.
        :param tx_amount_by_currency_id: the amount by the currency of the transaction.
        :param tx_sender_fee: the part of the tx fee paid by the sender
        :param tx_counterparty_fee: the part of the tx fee paid by the counterparty
        :param tx_quantities_by_good_id: a map from good id to the quantity of that good involved in the transaction.
        :param ledger_id: the ledger id
        :param info: a dictionary for arbitrary information
        """
        super().__init__(
            performative=performative,
            skill_callback_ids=skill_callback_ids,
            tx_id=tx_id,
            tx_sender_addr=tx_sender_addr,
            tx_counterparty_addr=tx_counterparty_addr,
            tx_amount_by_currency_id=tx_amount_by_currency_id,
            tx_sender_fee=tx_sender_fee,
            tx_counterparty_fee=tx_counterparty_fee,
            tx_quantities_by_good_id=tx_quantities_by_good_id,
            ledger_id=ledger_id,
            info=info,
            **kwargs
        )
        assert (
            self.check_consistency()
        ), "Transaction message initialization inconsistent."

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "Performative is not set."
        return TransactionMessage.Performative(self.get("performative"))

    @property
    def skill_callback_ids(self) -> List[str]:
        """Get the list of skill_callback_ids from the message."""
        assert self.is_set("skill_callback_ids"), "Skill_callback_ids is not set."
        return cast(List[str], self.get("skill_callback_ids"))

    @property
    def tx_id(self) -> str:
        """Get the transaction id."""
        assert self.is_set("tx_id"), "Transaction_id is not set."
        return cast(str, self.get("tx_id"))

    @property
    def tx_sender_addr(self) -> Address:
        """Get the address of the sender."""
        assert self.is_set("tx_sender_addr"), "Tx_sender_addr is not set."
        return cast(Address, self.get("tx_sender_addr"))

    @property
    def tx_counterparty_addr(self) -> Address:
        """Get the counterparty of the message."""
        assert self.is_set("tx_counterparty_addr"), "Counterparty is not set."
        return cast(Address, self.get("tx_counterparty_addr"))

    @property
    def tx_amount_by_currency_id(self) -> Dict[str, int]:
        """Get the currency id."""
        assert self.is_set(
            "tx_amount_by_currency_id"
        ), "Tx_amount_by_currency_id is not set."
        return cast(Dict[str, int], self.get("tx_amount_by_currency_id"))

    @property
    def tx_sender_fee(self) -> int:
        """Get the fee for the sender from the messgae."""
        assert self.is_set("tx_sender_fee"), "Tx_sender_fee is not set."
        return cast(int, self.get("tx_sender_fee"))

    @property
    def tx_counterparty_fee(self) -> int:
        """Get the fee for the counterparty from the messgae."""
        assert self.is_set("tx_counterparty_fee"), "Tx_counterparty_fee is not set."
        return cast(int, self.get("tx_counterparty_fee"))

    @property
    def tx_quantities_by_good_id(self) -> Dict[str, int]:
        """Get the quantities by good ids."""
        assert self.is_set(
            "tx_quantities_by_good_id"
        ), "Tx_quantities_by_good_id is not set."
        return cast(Dict[str, int], self.get("tx_quantities_by_good_id"))

    @property
    def ledger_id(self) -> LedgerId:
        """Get the ledger_id."""
        assert self.is_set("ledger_id"), "Ledger_id is not set."
        return cast(str, self.get("ledger_id"))

    @property
    def info(self) -> Dict[str, Any]:
        """Get the infos from the message."""
        assert self.is_set("info"), "Info is not set."
        return cast(Dict[str, Any], self.get("info"))

    @property
    def tx_digest(self) -> str:
        """Get the transaction digest."""
        assert self.is_set("tx_digest"), "Tx_digest is not set."
        return cast(str, self.get("tx_digest"))

    @property
    def signing_payload(self) -> Dict[str, Any]:
        """Get the signing payload."""
        assert self.is_set("signing_payload"), "signing_payload is not set."
        return cast(Dict[str, Any], self.get("signing_payload"))

    @property
    def tx_signature(self) -> str:
        """Get the transaction signature."""
        assert self.is_set("tx_signature"), "Tx_signature is not set."
        return cast(str, self.get("tx_signature"))

    @property
    def amount(self) -> int:
        """Get the amount."""
        return list(self.tx_amount_by_currency_id.values())[0]

    @property
    def currency_id(self) -> str:
        """Get the currency id."""
        return list(self.tx_amount_by_currency_id.keys())[0]

    @property
    def sender_amount(self) -> int:
        """Get the amount which the sender gets/pays as part of the tx."""
        return self.amount - self.tx_sender_fee

    @property
    def counterparty_amount(self) -> int:
        """Get the amount which the counterparty gets/pays as part of the tx."""
        return -self.amount - self.tx_counterparty_fee

    @property
    def fees(self) -> int:
        """Get the tx fees."""
        return self.tx_sender_fee + self.tx_counterparty_fee

    def check_consistency(self) -> bool:
        """
        Check that the data is consistent.

        :return: bool
        """
        try:
            assert isinstance(
                self.performative, TransactionMessage.Performative
            ), "Performative is not of correct type."
            assert isinstance(self.skill_callback_ids, list) and all(
                isinstance(s, str) for s in self.skill_callback_ids
            ), "Skill_callback_ids must be of type List[str]."
            assert isinstance(self.tx_id, str), "Tx_id must of type str."
            assert isinstance(
                self.tx_sender_addr, Address
            ), "Tx_sender_addr must be of type Address."
            assert isinstance(
                self.tx_counterparty_addr, Address
            ), "Tx_counterparty_addr must be of type Address."
            assert (
                self.tx_sender_addr != self.tx_counterparty_addr
            ), "Tx_sender_addr must be different of tx_counterparty_addr."
            assert isinstance(self.tx_amount_by_currency_id, dict) and all(
                (isinstance(key, str) and isinstance(value, int))
                for key, value in self.tx_amount_by_currency_id.items()
            ), "Tx_amount_by_currency_id must be of type Dict[str, int]."
            assert (
                len(self.tx_amount_by_currency_id) == 1
            ), "Cannot reference more than one currency."
            assert isinstance(
                self.tx_sender_fee, int
            ), "Tx_sender_fee must be of type int."
            assert (
                self.tx_sender_fee >= 0
            ), "Tx_sender_fee must be greater or equal to zero."
            assert isinstance(
                self.tx_counterparty_fee, int
            ), "Tx_counterparty_fee must be of type int."
            assert (
                self.tx_counterparty_fee >= 0
            ), "Tx_counterparty_fee must be greater or equal to zero."
            assert isinstance(self.tx_quantities_by_good_id, dict) and all(
                (isinstance(key, str) and isinstance(value, int))
                for key, value in self.tx_quantities_by_good_id.items()
            ), "Tx_quantities_by_good_id must be of type Dict[str, int]."
            assert (
                isinstance(self.ledger_id, str)
                and self.ledger_id in SUPPORTED_LEDGER_IDS
            ), ("Ledger_id must be str and " "must in the supported ledger ids.")
            assert isinstance(self.info, dict) and all(
                isinstance(key, str) for key in self.info.keys()
            ), "Info must be of type Dict[str, Any]."
            if not self.ledger_id == OFF_CHAIN:
                assert (
                    self.currency_id == SUPPORTED_CURRENCIES[self.ledger_id]
                ), "Inconsistent currency_id given ledger_id."
            if self.amount >= 0:
                assert (
                    self.sender_amount >= 0
                ), "Sender_amount must be positive when the sender is the payment receiver."
            else:
                assert (
                    self.counterparty_amount >= 0
                ), "Counterparty_amount must be positive when the counterpary is the payment receiver."

            if self.performative in {
                self.Performative.PROPOSE_FOR_SETTLEMENT,
                self.Performative.REJECTED_SETTLEMENT,
                self.Performative.FAILED_SETTLEMENT,
            }:
                assert len(self.body) == 11 or len(self.body) == 12
            elif self.performative == self.Performative.SUCCESSFUL_SETTLEMENT:
                assert isinstance(self.tx_digest, str), "Tx_digest must be of type str."
                assert len(self.body) == 12
            elif self.performative in {
                self.Performative.PROPOSE_FOR_SIGNING,
                self.Performative.REJECTED_SIGNING,
            }:
                assert isinstance(self.signing_payload, dict) and all(
                    isinstance(key, str) for key in self.signing_payload.keys()
                ), "Signing_payload must be of type Dict[str, Any]"
                assert len(self.body) == 12
            elif self.performative == self.Performative.SUCCESSFUL_SIGNING:
                assert isinstance(self.signing_payload, dict) and all(
                    isinstance(key, str) for key in self.signing_payload.keys()
                ), "Signing_payload must be of type Dict[str, Any]"
                assert isinstance(
                    self.tx_signature, bytes
                ), "Tx_signature must be of type bytes"
                assert len(self.body) == 13
            else:  # pragma: no cover
                raise ValueError("Performative not recognized.")

        except (AssertionError, KeyError):
            return False
        return True

    @classmethod
    def respond_settlement(
        cls,
        other: "TransactionMessage",
        performative: Performative,
        tx_digest: Optional[str] = None,
    ) -> "TransactionMessage":
        """
        Create response message.

        :param other: TransactionMessage
        :param performative: the performative
        :param tx_digest: the transaction digest
        :return: a transaction message object
        """
        if tx_digest is None:
            tx_msg = TransactionMessage(
                performative=performative,
                skill_callback_ids=other.skill_callback_ids,
                tx_id=other.tx_id,
                tx_sender_addr=other.tx_sender_addr,
                tx_counterparty_addr=other.tx_counterparty_addr,
                tx_amount_by_currency_id=other.tx_amount_by_currency_id,
                tx_sender_fee=other.tx_sender_fee,
                tx_counterparty_fee=other.tx_counterparty_fee,
                tx_quantities_by_good_id=other.tx_quantities_by_good_id,
                ledger_id=other.ledger_id,
                info=other.info,
            )
        else:
            tx_msg = TransactionMessage(
                performative=performative,
                skill_callback_ids=other.skill_callback_ids,
                tx_id=other.tx_id,
                tx_sender_addr=other.tx_sender_addr,
                tx_counterparty_addr=other.tx_counterparty_addr,
                tx_amount_by_currency_id=other.tx_amount_by_currency_id,
                tx_sender_fee=other.tx_sender_fee,
                tx_counterparty_fee=other.tx_counterparty_fee,
                tx_quantities_by_good_id=other.tx_quantities_by_good_id,
                ledger_id=other.ledger_id,
                info=other.info,
                tx_digest=tx_digest,
            )
        return tx_msg

    @classmethod
    def respond_signing(
        cls,
        other: "TransactionMessage",
        performative: Performative,
        tx_signature: Optional[str] = None,
    ) -> "TransactionMessage":
        """
        Create response message.

        :param other: TransactionMessage
        :param performative: the performative
        :param tx_digest: the transaction digest
        :return: a transaction message object
        """
        if tx_signature is None:
            tx_msg = TransactionMessage(
                performative=performative,
                skill_callback_ids=other.skill_callback_ids,
                tx_id=other.tx_id,
                tx_sender_addr=other.tx_sender_addr,
                tx_counterparty_addr=other.tx_counterparty_addr,
                tx_amount_by_currency_id=other.tx_amount_by_currency_id,
                tx_sender_fee=other.tx_sender_fee,
                tx_counterparty_fee=other.tx_counterparty_fee,
                tx_quantities_by_good_id=other.tx_quantities_by_good_id,
                ledger_id=other.ledger_id,
                info=other.info,
                signing_payload=other.signing_payload,
            )
        else:
            tx_msg = TransactionMessage(
                performative=performative,
                skill_callback_ids=other.skill_callback_ids,
                tx_id=other.tx_id,
                tx_sender_addr=other.tx_sender_addr,
                tx_counterparty_addr=other.tx_counterparty_addr,
                tx_amount_by_currency_id=other.tx_amount_by_currency_id,
                tx_sender_fee=other.tx_sender_fee,
                tx_counterparty_fee=other.tx_counterparty_fee,
                tx_quantities_by_good_id=other.tx_quantities_by_good_id,
                ledger_id=other.ledger_id,
                info=other.info,
                signing_payload=other.signing_payload,
                tx_signature=tx_signature,
            )
        return tx_msg
