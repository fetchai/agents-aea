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

"""This package contains handlers for the fetch_beacon skill."""

from typing import Any, Dict, Optional, cast

from aea_ledger_ethereum import EthereumApi

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.fetch_beacon.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
)


def keccak256(input_: bytes) -> bytes:
    """Compute hash."""
    return bytes(bytearray.fromhex(EthereumApi.get_hash(input_)[2:]))


class LedgerApiHandler(Handler):
    """Implement the ledger api handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        self.context.logger.info("Handling ledger api msg")

        ledger_api_msg = cast(LedgerApiMessage, message)

        # recover dialogue
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self._handle_unidentified_dialogue(ledger_api_msg)
            return

        # handle message
        if ledger_api_msg.performative is LedgerApiMessage.Performative.STATE:
            self._handle_state(ledger_api_msg)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)  # pragma: nocover
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ledger_api_msg: the message
        """
        self.context.logger.info(
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_state(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of state performative.

        :param ledger_api_msg: the ledger api message
        """

        self.context.logger.debug(f"Handling ledger API message: {ledger_api_msg}")

        block_info = ledger_api_msg.state.body  # type: Dict[str, Any]

        # get entropy and block data
        entropy = (
            block_info.get("block", {})
            .get("header", {})
            .get("entropy", {})
            .get("group_signature", None)
        )
        block_hash = block_info.get("block_id", {}).get("hash", {})
        block_height_str = (
            block_info.get("block", {}).get("header", {}).get("height", None)
        )

        if block_height_str:
            block_height = int(block_height_str)  # type: Optional[int]
        else:
            block_height = None  #  pragma: nocover

        if entropy is None:  # pragma: nocover
            self.context.logger.info("entropy not present")
        elif block_height is None:  # pragma: nocover
            self.context.logger.info("block height not present")
        else:
            beacon_data = {
                "entropy": keccak256(entropy.encode("utf-8")),
                "block_hash": bytes.fromhex(block_hash),
                "block_height": block_height,
            }
            self.context.logger.info(
                "Beacon info: "
                + str({"block_height": block_height, "entropy": entropy})
            )
            self.context.shared_state["observation"] = {"beacon": beacon_data}

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(  # pragma: nocover
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
            )
        )
