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

"""This package contains a scaffold of a handler."""

from typing import Optional, cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.registration_aw1.dialogues import (
    RegisterDialogue,
    RegisterDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.registration_aw1.strategy import Strategy


class AW1RegistrationHandler(Handler):
    """This class handles register messages."""

    SUPPORTED_PROTOCOL = RegisterMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        register_msg = cast(RegisterMessage, message)

        # recover dialogue
        register_dialogues = cast(RegisterDialogues, self.context.register_dialogues)
        register_dialogue = cast(
            Optional[RegisterDialogue], register_dialogues.update(register_msg)
        )
        if register_dialogue is None:
            self._handle_unidentified_dialogue(register_msg)
            return

        # handle message
        if register_msg.performative is RegisterMessage.Performative.SUCCESS:
            self._handle_success(register_msg, register_dialogue)
        elif register_msg.performative is RegisterMessage.Performative.ERROR:
            self._handle_error(register_msg, register_dialogue)
        else:
            self._handle_invalid(register_msg, register_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, register_msg: RegisterMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param register_msg: the message
        """
        self.context.logger.info(
            f"received invalid register_msg message={register_msg}, unidentified dialogue."
        )

    def _handle_success(
        self, register_msg: RegisterMessage, register_dialogue: RegisterDialogue
    ) -> None:
        """
        Handle an register message.

        :param register_msg: the register message
        :param register_dialogue: the dialogue
        """
        self.context.logger.debug(
            f"received register_msg success message={register_msg} in dialogue={register_dialogue}."
        )
        self.context.logger.info(
            f"received register message success, info={register_msg.info}. Stop me now!"
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_registered = True
        strategy.is_registration_pending = False
        strategy.is_ready_to_register = False

        if strategy.announce_termination_key is not None:
            self.context.shared_state[strategy.announce_termination_key] = True

    def _handle_error(
        self, register_msg: RegisterMessage, register_dialogue: RegisterDialogue
    ) -> None:
        """
        Handle an register message.

        :param register_msg: the register message
        :param register_dialogue: the dialogue
        """
        self.context.logger.debug(
            f"received register_msg error message={register_msg} in dialogue={register_dialogue}."
        )
        self.context.logger.info(
            f"received register message error, error_msg={register_msg.error_msg}. Stop me now!"
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_registration_pending = False
        strategy.is_ready_to_register = False

    def _handle_invalid(
        self, register_msg: RegisterMessage, register_dialogue: RegisterDialogue
    ) -> None:
        """
        Handle an register message.

        :param register_msg: the register message
        :param register_dialogue: the dialogue
        """
        self.context.logger.warning(
            f"cannot handle register_msg message of performative={register_msg.performative} in dialogue={register_dialogue}."
        )


class SigningHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        signing_msg = cast(SigningMessage, message)

        # recover dialogue
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        if signing_dialogue is None:
            self._handle_unidentified_dialogue(signing_msg)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_MESSAGE:
            self._handle_signed_message(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param signing_msg: the message
        """
        self.context.logger.info(
            f"received invalid signing message={signing_msg}, unidentified dialogue."
        )

    def _handle_signed_message(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle a signed message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.debug(
            f"received signing message from decision maker, message={signing_msg} in dialogue={signing_dialogue}"
        )
        self.context.logger.info(
            f"received signing message from decision maker, signature={signing_msg.signed_message.body} stored!"
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.signature_of_ethereum_address = signing_msg.signed_message.body
        strategy.is_ready_to_register = True

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info(
            f"transaction signing was not successful. Error_code={signing_msg.error_code} in dialogue={signing_dialogue}"
        )

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.warning(
            f"cannot handle signing message of performative={signing_msg.performative} in dialogue={signing_dialogue}."
        )
