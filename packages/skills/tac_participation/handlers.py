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

"""This package contains the handlers."""

import logging
from typing import Dict, List, cast, TYPE_CHECKING

from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.protocols.base import Message
from aea.protocols.oef.message import OEFMessage
from aea.skills.base import Handler

if TYPE_CHECKING:
    from packages.protocols.tac.message import TACMessage
    from packages.protocols.tac.serialization import TACSerializer
    from packages.skills.tac_participation.game import Game, Phase
    from packages.skills.tac_participation.search import Search
else:
    from tac_protocol.message import TACMessage
    from tac_protocol.serialization import TACSerializer
    from tac_participation_skill.game import Game, Phase
    from tac_participation_skill.search import Search


Address = str

logger = logging.getLogger("aea.tac_participation_skill")


class OEFHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the echo behaviour."""
        super().__init__(**kwargs)
        # self._rejoin = False

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        oef_message = cast(OEFMessage, message)
        oef_type = oef_message.get("type")

        logger.debug("[{}]: Handling OEF message. type={}".format(self.context.agent_name, oef_type))
        if oef_type == OEFMessage.Type.SEARCH_RESULT:
            self._on_search_result(oef_message)
        elif oef_type == OEFMessage.Type.OEF_ERROR:
            self._on_oef_error(oef_message)
        elif oef_type == OEFMessage.Type.DIALOGUE_ERROR:
            self._on_dialogue_error(oef_message)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _on_oef_error(self, oef_error: OEFMessage) -> None:
        """
        Handle an OEF error message.

        :param oef_error: the oef error

        :return: None
        """
        logger.error("[{}]: Received OEF error: answer_id={}, operation={}"
                     .format(self.context.agent_name, oef_error.get("id"), oef_error.get("operation")))

    def _on_dialogue_error(self, dialogue_error: OEFMessage) -> None:
        """
        Handle a dialogue error message.

        :param dialogue_error: the dialogue error message

        :return: None
        """
        logger.error("[{}]: Received Dialogue error: answer_id={}, dialogue_id={}, origin={}"
                     .format(self.context.agent_name, dialogue_error.get("id"), dialogue_error.get("dialogue_id"), dialogue_error.get("origin")))

    def _on_search_result(self, search_result: OEFMessage) -> None:
        """
        Split the search results from the OEF.

        :param search_result: the search result

        :return: None
        """
        search = cast(Search, self.context.search)
        search_id = search_result.get("id")
        agents = search_result.get("agents")
        agents = cast(List[str], agents)
        logger.debug("[{}]: on search result: {} {}".format(self.context.agent_name, search_id, agents))
        if search_id in search.ids_for_tac:
            self._on_controller_search_result(agents)
        else:
            logger.debug("[{}]: Unknown search id: search_id={}".format(self.context.agent_name, search_id))

    def _on_controller_search_result(self, agent_pbks: List[Address]) -> None:
        """
        Process the search result for a controller.

        :param agent_pbks: list of agent pbks

        :return: None
        """
        game = cast(Game, self.context.game)
        if game.phase.value != Phase.PRE_GAME.value:
            logger.debug("[{}]: Ignoring controller search result, the agent is already competing.".format(self.context.agent_name))
            return

        if len(agent_pbks) == 0:
            logger.debug("[{}]: Couldn't find the TAC controller. Retrying...".format(self.context.agent_name))
        elif len(agent_pbks) > 1:
            logger.error("[{}]: Found more than one TAC controller. Retrying...".format(self.context.agent_name))
        # elif self._rejoin:
        #     logger.debug("[{}]: Found the TAC controller. Rejoining...".format(self.context.agent_name))
        #     controller_pbk = agent_pbks[0]
        #     self._rejoin_tac(controller_pbk)
        else:
            logger.info("[{}]: Found the TAC controller. Registering...".format(self.context.agent_name))
            controller_pbk = agent_pbks[0]
            self._register_to_tac(controller_pbk)

    def _register_to_tac(self, controller_pbk: Address) -> None:
        """
        Register to active TAC Controller.

        :param controller_pbk: the public key of the controller.

        :return: None
        """
        game = cast(Game, self.context.game)
        game.update_expected_controller_pbk(controller_pbk)
        game.update_game_phase(Phase.GAME_REGISTRATION)
        tac_msg = TACMessage(tac_type=TACMessage.Type.REGISTER, agent_name=self.context.agent_name)
        tac_bytes = TACSerializer().encode(tac_msg)
        self.context.outbox.put_message(to=controller_pbk, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

    # def _rejoin_tac(self, controller_pbk: Address) -> None:
    #     """
    #     Rejoin the TAC run by a Controller.

    #     :param controller_pbk: the public key of the controller.

    #     :return: None
    #     """
    #     game = cast(Game, self.context.game)
    #     game.update_expected_controller_pbk(controller_pbk)
    #     game.update_game_phase(Phase.GAME_SETUP)
    #     tac_msg = TACMessage(tac_type=TACMessage.Type.GET_STATE_UPDATE)
    #     tac_bytes = TACSerializer().encode(tac_msg)
    #     self.context.outbox.put_message(to=controller_pbk, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)


class TACHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = TACMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        tac_msg = cast(TACMessage, message)
        tac_msg_type = TACMessage.Type(tac_msg.get("type"))
        game = cast(Game, self.context.game)
        logger.debug("[{}]: Handling controller response. type={}".format(self.context.agent_name, tac_msg_type))
        try:
            if sender != game.expected_controller_pbk:
                raise ValueError("The sender of the message is not the controller agent we registered with.")

            if tac_msg_type == TACMessage.Type.TAC_ERROR:
                self._on_tac_error(tac_msg, sender)
            elif game.phase.value == Phase.PRE_GAME.value:
                raise ValueError("We do not expect a controller agent message in the pre game phase.")
            elif game.phase.value == Phase.GAME_REGISTRATION.value:
                if tac_msg_type == TACMessage.Type.GAME_DATA:
                    self._on_start(tac_msg, sender)
                elif tac_msg_type == TACMessage.Type.CANCELLED:
                    self._on_cancelled()
            elif game.phase.value == Phase.GAME.value:
                if tac_msg_type == TACMessage.Type.TRANSACTION_CONFIRMATION:
                    self._on_transaction_confirmed(tac_msg, sender)
                elif tac_msg_type == TACMessage.Type.CANCELLED:
                    self._on_cancelled()
                # elif tac_msg_type == TACMessage.Type.STATE_UPDATE:
                #     self._on_state_update(tac_msg, sender)
            elif game.phase.value == Phase.POST_GAME.value:
                raise ValueError("We do not expect a controller agent message in the post game phase.")
        except ValueError as e:
            logger.warning(str(e))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _on_tac_error(self, tac_message: TACMessage, controller_pbk: Address) -> None:
        """
        Handle 'on tac error' event emitted by the controller.

        :param error: the error object

        :return: None
        """
        error_code = TACMessage.ErrorCode(tac_message.get("error_code"))
        logger.error("[{}]: Received error from the controller. error_msg={}".format(self.context.agent_name, TACMessage._from_ec_to_msg.get(error_code)))
        if error_code == TACMessage.ErrorCode.TRANSACTION_NOT_VALID:
            start_idx_of_tx_id = len("Error in checking transaction: ")
            transaction_id = cast(str, tac_message.get("error_msg"))[start_idx_of_tx_id:]
            logger.warning("[{}]: Received error on transaction id: {}".format(self.context.agent_name, transaction_id))

    def _on_start(self, tac_message: TACMessage, controller_pbk: Address) -> None:
        """
        Handle the 'start' event emitted by the controller.

        :param tac_message: the game data

        :return: None
        """
        logger.info("[{}]: Received start event from the controller. Starting to compete...".format(self.context.agent_name))
        game = cast(Game, self.context.game)
        game.init(tac_message, controller_pbk)
        game.update_game_phase(Phase.GAME)

    def _on_cancelled(self) -> None:
        """
        Handle the cancellation of the competition from the TAC controller.

        :return: None
        """
        logger.info("[{}]: Received cancellation from the controller.".format(self.context.agent_name))
        game = cast(Game, self.context.game)
        game.update_game_phase(Phase.POST_GAME)

    def _on_transaction_confirmed(self, message: TACMessage, controller_pbk: Address) -> None:
        """
        Handle 'on transaction confirmed' event emitted by the controller.

        :param tx_confirmation: the transaction confirmation

        :return: None
        """
        logger.info("[{}]: Received transaction confirmation from the controller: transaction_id={}".format(self.context.agent_name, message.get("transaction_id")))
        state_update_msg = StateUpdateMessage(performative=StateUpdateMessage.Performative.APPLY,
                                              amount_by_currency_pbk=cast(Dict[str, int], message.get("amount_by_currency_pbk")),
                                              quantities_by_good_pbk=cast(Dict[str, int], message.get("quantities_by_good_pbk")))
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)

    # def _on_state_update(self, tac_message: TACMessage, controller_pbk: Address) -> None:
    #     """
    #     Update the game instance with a State Update from the controller.

    #     :param tac_message: the state update
    #     :param controller_pbk: the public key of the controller

    #     :return: None
    #     """
    #     game = cast(Game, self.context.game)
    #     game.init(tac_message, controller_pbk)
    #     game.update_game_phase(Phase.GAME)
    #     # for tx in message.get("transactions"):
    #     #     self.agent_state.update(tx, tac_message.get("initial_state").get("tx_fee"))
    #     self.context.state_update_queue =
    #     self._initial_agent_state = AgentStateUpdate(game_data.money, game_data.endowment, game_data.utility_params)
    #     self._agent_state = AgentState(game_data.money, game_data.endowment, game_data.utility_params)
    #     # if self.strategy.is_world_modeling:
    #     #     opponent_pbks = self.game_configuration.agent_pbks
    #     #     opponent_pbks.remove(agent_pbk)
    #     #     self._world_state = WorldState(opponent_pbks, self.game_configuration.good_pbks, self.initial_agent_state)

    def _on_dialogue_error(self, tac_message: TACMessage, controller_pbk: Address) -> None:
        """
        Handle dialogue error event emitted by the controller.

        :param message: the dialogue error message
        :param controller_pbk: the address of the controller

        :return: None
        """
        logger.warning("[{}]: Received Dialogue error from: details={}, sender={}".format(self.context.agent_name, tac_message.get("details"), controller_pbk))

    # def _request_state_update(self) -> None:
    #     """
    #     Request current agent state from TAC Controller.

    #     :return: None
    #     """
    #     tac_msg = TACMessage(tac_type=TACMessage.Type.GET_STATE_UPDATE)
    #     tac_bytes = TACSerializer().encode(tac_msg)
    #     game = cast(Game, self.context.game)
    #     self.context.outbox.put_message(to=game.expected_controller_pbk, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)
