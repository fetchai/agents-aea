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

"""This package contains the handlers for the oracle aggregation skill."""

from typing import Any, Dict, Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.consensus.message import ConsensusMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.oracle_aggregation.dialogues import (
    ConsensusDialogue,
    ConsensusDialogues,
    DefaultDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.oracle_aggregation.strategy import GenericStrategy


class GenericConsensusHandler(Handler):
    """This class implements a Consensus handler."""

    SUPPORTED_PROTOCOL = ConsensusMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        consensus_msg = cast(ConsensusMessage, message)

        # recover dialogue
        consensus_dialogues = cast(ConsensusDialogues, self.context.consensus_dialogues)
        consensus_dialogue = cast(
            ConsensusDialogue, consensus_dialogues.update(consensus_msg)
        )
        if consensus_dialogue is None:
            self._handle_unidentified_dialogue(consensus_msg)
            return

        # handle message
        if consensus_msg.performative == ConsensusMessage.Performative.OBSERVATION:
            self._handle_observation(consensus_msg)
        elif consensus_msg.performative == ConsensusMessage.Performative.AGGREGATION:
            self._handle_aggregation(consensus_msg)
        else:
            self._handle_invalid(consensus_msg, consensus_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, consensus_msg: ConsensusMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param consensus_msg: the message
        """
        self.context.logger.info(
            "received invalid consensus message={}, unidentified dialogue.".format(
                consensus_msg
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=consensus_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"consensus_message": consensus_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def get_observation_from_message(self, obs_msg: ConsensusMessage) -> Dict[str, Any]:
        """Extract the observation from an observation message"""
        obs = {
            "value": obs_msg.value,
            "time": obs_msg.time,
            "source": obs_msg.source,
            "signature": obs_msg.signature,
        }
        return obs

    def _handle_observation(self, obs_msg: ConsensusMessage) -> None:
        """
        Handle the observation.

        :param obs_msg: the message
        :param consensus_dialogue: the dialogue object
        :return: None
        """

        self.context.logger.info(
            "received observation from sender={}".format(obs_msg.sender[-5:])
        )

        strategy = cast(GenericStrategy, self.context.strategy)
        obs = self.get_observation_from_message(obs_msg)

        strategy.add_observation(obs_msg.sender, obs)
        strategy.aggregate_observations()

        self.context.logger.info(f"observation: {obs}")

    def _handle_aggregation(self, consensus_msg: ConsensusMessage) -> None:
        """
        Handle the aggregation.

        :param consensus_msg: the message
        :param consensus_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "received aggregation from sender={}".format(consensus_msg.sender[-5:])
        )

    def _handle_invalid(
        self, consensus_msg: ConsensusMessage, consensus_dialogue: ConsensusDialogue
    ) -> None:
        """
        Handle a consensus message of invalid performative.

        :param consensus_msg: the message
        :param consensus_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.warning(
            "cannot handle consensus message of performative={} in dialogue={}.".format(
                consensus_msg.performative, consensus_dialogue
            )
        )


class GenericOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info(
                f"found no agents in dialogue={oef_search_dialogue}, continue searching."
            )
            return
        strategy = cast(GenericStrategy, self.context.strategy)
        self.context.logger.info(
            "found agents={}.".format(
                list(map(lambda x: x[-5:], oef_search_msg.agents)),
            )
        )
        consensus_dialogues = cast(ConsensusDialogues, self.context.consensus_dialogues)
        strategy.add_peers(oef_search_msg.agents)
        obs = strategy.observation
        for counterparty in strategy.peers:
            obs_msg, _ = consensus_dialogues.create(
                counterparty=counterparty,
                performative=ConsensusMessage.Performative.OBSERVATION,
                **obs,
            )
            self.context.outbox.put_message(message=obs_msg)
            self.context.logger.info(
                "sending observation to peer={}".format(counterparty[-5:])
            )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
