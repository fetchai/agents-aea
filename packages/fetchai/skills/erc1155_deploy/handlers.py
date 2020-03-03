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

"""This package contains the handlers of a generic seller AEA."""

from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.skills.generic_seller.dialogues import Dialogue, Dialogues
from packages.fetchai.skills.generic_seller.strategy import Strategy


class FIPAHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        # convenience representations
        fipa_msg = cast(FIPAMessage, message)
        dialogue_reference = fipa_msg.dialogue_reference

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(
            fipa_msg, self.context.agent_address
        ):
            dialogue = cast(
                Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_address)
            )
            dialogue.incoming_extend(fipa_msg)
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg):
            dialogue = cast(
                Dialogue,
                dialogues.create_opponent_initiated(
                    message.counterparty,
                    dialogue_reference=dialogue_reference,
                    is_seller=True,
                ),
            )
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, msg: FIPAMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param msg: the message

        :return: None
        """
        self.context.logger.info(
            "[{}]: unidentified dialogue.".format(self.context.agent_name)
        )
        default_msg = DefaultMessage(
            type=DefaultMessage.Type.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
            error_msg="Invalid dialogue.",
            error_data="fipa_message",
        )  # TODO: send FIPASerializer().encode(msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(default_msg),
        )

    def _handle_inform(self, msg: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled, send the data, otherwise do nothing.

        :param msg: the message
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )

        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_ledger_tx and ("transaction_digest" in msg.info.keys()):
            tx_digest = msg.info["transaction_digest"]
            self.context.logger.info(
                "[{}]: checking whether transaction={} has been received ...".format(
                    self.context.agent_name, tx_digest
                )
            )
            proposal = cast(Description, dialogue.proposal)
            ledger_id = cast(str, proposal.values.get("ledger_id"))
            is_valid = self.context.ledger_apis.is_tx_valid(
                ledger_id,
                tx_digest,
                self.context.agent_addresses[ledger_id],
                msg.counterparty,
                cast(str, proposal.values.get("tx_nonce")),
                cast(int, proposal.values.get("price")),
            )
            # TODO: check the tx_digest references a transaction with the correct terms
            if is_valid:
                token_balance = self.context.ledger_apis.token_balance(
                    ledger_id, cast(str, self.context.agent_addresses.get(ledger_id))
                )
                self.context.logger.info(
                    "[{}]: transaction={} settled, new balance={}. Sending data to sender={}".format(
                        self.context.agent_name,
                        tx_digest,
                        token_balance,
                        msg.counterparty[-5:],
                    )
                )
                inform_msg = FIPAMessage(
                    message_id=new_message_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=new_target,
                    performative=FIPAMessage.Performative.INFORM,
                    info=dialogue.data_for_sale,
                )
                dialogue.outgoing_extend(inform_msg)
                self.context.outbox.put_message(
                    to=msg.counterparty,
                    sender=self.context.agent_address,
                    protocol_id=FIPAMessage.protocol_id,
                    message=FIPASerializer().encode(inform_msg),
                )
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(
                    Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
                )
            else:
                self.context.logger.info(
                    "[{}]: transaction={} not settled, aborting".format(
                        self.context.agent_name, tx_digest
                    )
                )
        elif "Done" in msg.info.keys():
            inform_msg = FIPAMessage(
                message_id=new_message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=new_target,
                performative=FIPAMessage.Performative.INFORM,
                info=dialogue.data_for_sale,
            )
            dialogue.outgoing_extend(inform_msg)
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(inform_msg),
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.SUCCESSFUL, dialogue.is_self_initiated
            )
        else:
            self.context.logger.warning(
                "[{}]: did not receive transaction digest from sender={}.".format(
                    self.context.agent_name, msg.counterparty[-5:]
                )
            )


class TransactionHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        tx_msg_response = cast(TransactionMessage, message)
        contract = self.context.contracts.erc1155
        if tx_msg_response.tx_id == "contract_deploy":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            result = ledger_api.get_transaction_status(  # type: ignore
                tx_signed
            )
            self.context.logger.info(result)
            contract.set_address(ledger_api, result.contract_Address)
            self.context.logger.info(contract.is_deployed)
        elif tx_msg_response.tx_id == "contract_create_batch":
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            result = ledger_api.send_raw_transaction(  # type: ignore
                tx_msg_response.signed_payload.get("tx_signed")
            )
            self.context.logger.info(result)
        elif tx_msg_response.tx_id == "contract_mint_batch":
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            result = ledger_api.send_raw_transaction(  # type: ignore
                tx_msg_response.signed_payload.get("tx_signed")
            )
            self.context.logger.info(result)
            contract.is_items_created = True
            self.context.logger.info("Ask the contract about my balances:")
            result = contract.get_balance_of_batch(address=self.context.agent_address)
            self.context.logger.info(result)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
