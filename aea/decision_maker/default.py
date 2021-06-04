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

"""This module contains the decision maker class."""

from typing import Any, Dict

from aea.common import Address
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMakerHandler as BaseDecisionMakerHandler
from aea.helpers.transaction.base import SignedMessage, SignedTransaction
from aea.identity.base import Identity
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue


class DecisionMakerHandler(BaseDecisionMakerHandler):
    """This class implements the decision maker."""

    # pylint: disable=import-outside-toplevel
    from packages.fetchai.protocols.signing.dialogues import (  # noqa: F811
        SigningDialogue,
    )
    from packages.fetchai.protocols.signing.dialogues import (  # noqa: F811
        SigningDialogues as BaseSigningDialogues,
    )
    from packages.fetchai.protocols.signing.message import SigningMessage  # noqa: F811

    class SigningDialogues(BaseSigningDialogues):
        """This class keeps track of all oef_search dialogues."""

        def __init__(self, self_address: Address, **kwargs: Any) -> None:
            """
            Initialize dialogues.

            :param self_address: the address of the entity for whom dialogues are maintained
            :param kwargs: the keyword arguments
            """

            def role_from_first_message(  # pylint: disable=unused-argument
                message: Message, receiver_address: Address
            ) -> BaseDialogue.Role:
                """Infer the role of the agent from an incoming/outgoing first message

                :param message: an incoming/outgoing first message
                :param receiver_address: the address of the receiving agent
                :return: The role of the agent
                """
                from packages.fetchai.protocols.signing.dialogues import (  # pylint: disable=import-outside-toplevel
                    SigningDialogue,
                )

                return SigningDialogue.Role.DECISION_MAKER

            # pylint: disable=import-outside-toplevel
            from packages.fetchai.protocols.signing.dialogues import (
                SigningDialogues as BaseSigningDialogues,
            )

            BaseSigningDialogues.__init__(
                self,
                self_address=self_address,
                role_from_first_message=role_from_first_message,
                **kwargs,
            )

    signing_dialogue_class = SigningDialogue
    signing_msg_class = SigningMessage

    __slots__ = ("signing_dialogues",)

    def __init__(
        self, identity: Identity, wallet: Wallet, config: Dict[str, Any]
    ) -> None:
        """
        Initialize the decision maker.

        :param identity: the identity
        :param wallet: the wallet
        :param config: the user defined configuration of the handler
        """
        kwargs: Dict[str, Any] = {}
        super().__init__(
            identity=identity, wallet=wallet, config=config, **kwargs,
        )
        self.signing_dialogues = DecisionMakerHandler.SigningDialogues(
            self.self_address
        )

    def handle(self, message: Message) -> None:
        """
        Handle an internal message from the skills.

        :param message: the internal message
        """
        if isinstance(message, self.signing_msg_class):
            self._handle_signing_message(message)
        else:  # pragma: no cover
            self.logger.error(
                "[{}]: cannot handle message={} of type={}".format(
                    self.agent_name, message, type(message)
                )
            )

    def _handle_signing_message(self, signing_msg: SigningMessage) -> None:
        """
        Handle a signing message.

        :param signing_msg: the transaction message
        """
        signing_dialogue = self.signing_dialogues.update(signing_msg)  # type: ignore
        if signing_dialogue is None or not isinstance(
            signing_dialogue, self.signing_dialogue_class
        ):  # pragma: no cover
            self.logger.error(
                "[{}]: Could not construct signing dialogue. Aborting!".format(
                    self.agent_name
                )
            )
            return

        if signing_msg.performative == self.signing_msg_class.Performative.SIGN_MESSAGE:
            self._handle_message_signing(signing_msg, signing_dialogue)
        elif (
            signing_msg.performative
            == self.signing_msg_class.Performative.SIGN_TRANSACTION
        ):
            self._handle_transaction_signing(signing_msg, signing_dialogue)
        else:  # pragma: no cover
            self.logger.error(
                "[{}]: Unexpected transaction message performative".format(
                    self.agent_name
                )
            )

    def _handle_message_signing(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle a message for signing.

        :param signing_msg: the signing message
        :param signing_dialogue: the signing dialogue
        """
        performative = self.signing_msg_class.Performative.ERROR
        kwargs = {
            "error_code": self.signing_msg_class.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        }  # type: Dict[str, Any]
        signed_message = self.wallet.sign_message(
            signing_msg.raw_message.ledger_id,
            signing_msg.raw_message.body,
            signing_msg.raw_message.is_deprecated_mode,
        )
        if signed_message is not None:
            performative = self.signing_msg_class.Performative.SIGNED_MESSAGE
            kwargs.pop("error_code")
            kwargs["signed_message"] = SignedMessage(
                signing_msg.raw_message.ledger_id,
                signed_message,
                signing_msg.raw_message.is_deprecated_mode,
            )
        signing_msg_response = signing_dialogue.reply(
            performative=performative, target_message=signing_msg, **kwargs,
        )
        self.message_out_queue.put(signing_msg_response)

    def _handle_transaction_signing(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle a transaction for signing.

        :param signing_msg: the signing message
        :param signing_dialogue: the signing dialogue
        """
        performative = self.signing_msg_class.Performative.ERROR
        kwargs = {
            "error_code": self.signing_msg_class.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
        }  # type: Dict[str, Any]
        signed_tx = self.wallet.sign_transaction(
            signing_msg.raw_transaction.ledger_id, signing_msg.raw_transaction.body
        )
        if signed_tx is not None:
            performative = self.signing_msg_class.Performative.SIGNED_TRANSACTION
            kwargs.pop("error_code")
            kwargs["signed_transaction"] = SignedTransaction(
                signing_msg.raw_transaction.ledger_id, signed_tx
            )
        signing_msg_response = signing_dialogue.reply(
            performative=performative, target_message=signing_msg, **kwargs,
        )
        self.message_out_queue.put(signing_msg_response)
