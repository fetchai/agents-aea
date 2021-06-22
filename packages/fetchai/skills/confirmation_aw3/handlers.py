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

"""This package contains the handlers of the agent."""

from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.confirmation_aw3.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
)
from packages.fetchai.skills.confirmation_aw3.strategy import Strategy
from packages.fetchai.skills.generic_buyer.handlers import (
    GenericFipaHandler,
    GenericLedgerApiHandler,
    GenericOefSearchHandler,
    GenericSigningHandler,
)


FipaHandler = GenericFipaHandler
LedgerApiHandler = GenericLedgerApiHandler
OefSearchHandler = GenericOefSearchHandler
SigningHandler = GenericSigningHandler


class DefaultHandler(Handler):
    """This class implements the default handler."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        default_msg = cast(DefaultMessage, message)

        # recover dialogue
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_dialogue = cast(DefaultDialogue, default_dialogues.update(default_msg))
        if default_dialogue is None:
            self._handle_unidentified_dialogue(default_msg)
            return

        # handle message
        if default_msg.performative == DefaultMessage.Performative.BYTES:
            self._handle_bytes(default_msg, default_dialogue)
        else:
            self._handle_invalid(default_msg, default_dialogue)

    def _handle_unidentified_dialogue(self, default_msg: DefaultMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param default_msg: the message
        """
        self.context.logger.info(
            f"received invalid default message={default_msg}, unidentified dialogue."
        )

    def _handle_bytes(
        self, default_msg: DefaultMessage, default_dialogue: DefaultDialogue
    ) -> None:
        """
        Handle a default message of invalid performative.

        :param default_msg: the message
        :param default_dialogue: the default dialogue
        """
        strategy = cast(Strategy, self.context.strategy)
        if default_msg.sender == strategy.aw1_aea:
            try:
                confirmed_aea, developer_handle = default_msg.content.decode(
                    "utf-8"
                ).split("_")
            except Exception:  # pylint: disable=broad-except
                confirmed_aea, developer_handle = "", ""
            if not LedgerApis.is_valid_address("fetchai", confirmed_aea):
                self.context.logger.warning(
                    f"received invalid address={confirmed_aea} in dialogue={default_dialogue}."
                )
                return
            if developer_handle == "":
                self.context.logger.warning(
                    f"received invalid developer_handle={developer_handle}."
                )
                return
            self.context.logger.info(
                f"adding confirmed_aea={confirmed_aea} with developer_handle={developer_handle} to db."
            )
            strategy.register_counterparty(confirmed_aea, developer_handle)
        else:
            self.context.logger.warning(
                f"cannot handle default message of performative={default_msg.performative} in dialogue={default_dialogue}. Invalid sender={default_msg.sender}"
            )

    def _handle_invalid(
        self, default_msg: DefaultMessage, default_dialogue: DefaultDialogue
    ) -> None:
        """
        Handle a default message of invalid performative.

        :param default_msg: the message
        :param default_dialogue: the default dialogue
        """
        self.context.logger.warning(
            f"cannot handle default message of performative={default_msg.performative} in dialogue={default_dialogue}."
        )

    def teardown(self) -> None:
        """Implement the handler teardown."""


class HttpHandler(Handler):
    """This implements the http handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))
        if http_dialogue is None:
            self._handle_unidentified_dialogue(http_msg)
            return

        # handle message
        if http_msg.performative == HttpMessage.Performative.RESPONSE:
            self._handle_response(http_msg, http_dialogue)
        else:
            self._handle_invalid(http_msg, http_dialogue)

    def _handle_unidentified_dialogue(self, http_msg: HttpMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param http_msg: the message
        """
        self.context.logger.info(
            "received invalid http message={}, unidentified dialogue.".format(http_msg)
        )

    def _handle_response(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http response.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.info(
            "received http response with status_code={}, status_text={} and body={!r} in dialogue={}".format(
                http_msg.status_code, http_msg.status_text, http_msg.body, http_dialogue
            )
        )

    def _handle_invalid(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle an invalid http message.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        self.context.logger.warning(
            "cannot handle http message of performative={} in dialogue={}.".format(
                http_msg.performative, http_dialogue
            )
        )

    def teardown(self) -> None:
        """Implement the handler teardown."""
