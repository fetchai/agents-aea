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

from packages.fetchai.protocols.aggregation.message import AggregationMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_aggregation.behaviours import SearchBehaviour
from packages.fetchai.skills.simple_aggregation.dialogues import (
    AggregationDialogue,
    AggregationDialogues,
    DefaultDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.simple_aggregation.strategy import AggregationStrategy


def get_observation_from_message(obs_msg: AggregationMessage) -> Dict[str, Any]:
    """
    Extract the observation from an observation message

    :param obs_msg: the message
    :return: the observation dict
    """
    obs = {
        "value": obs_msg.value,
        "time": obs_msg.time,
        "source": obs_msg.source,
        "signature": obs_msg.signature,
    }
    return obs


class AggregationHandler(Handler):
    """This class implements a simple aggregation handler."""

    SUPPORTED_PROTOCOL = AggregationMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        aggregation_msg = cast(AggregationMessage, message)

        # recover dialogue
        aggregation_dialogues = cast(
            AggregationDialogues, self.context.aggregation_dialogues
        )
        aggregation_dialogue = cast(
            AggregationDialogue, aggregation_dialogues.update(aggregation_msg)
        )
        if aggregation_dialogue is None:
            self._handle_unidentified_dialogue(aggregation_msg)
            return

        # handle message
        if aggregation_msg.performative == AggregationMessage.Performative.OBSERVATION:
            self._handle_observation(aggregation_msg)
        elif (
            aggregation_msg.performative == AggregationMessage.Performative.AGGREGATION
        ):
            self._handle_aggregation(aggregation_msg)
        else:
            self._handle_invalid(
                aggregation_msg, aggregation_dialogue
            )  # pragma: nocover

    def _handle_unidentified_dialogue(
        self, aggregation_msg: AggregationMessage
    ) -> None:
        """
        Handle an unidentified dialogue.

        :param aggregation_msg: the message
        """
        self.context.logger.info(
            "received invalid aggregation message={}, unidentified dialogue.".format(
                aggregation_msg
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=aggregation_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"aggregation_message": aggregation_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _handle_observation(self, obs_msg: AggregationMessage) -> None:
        """
        Handle the observation.

        :param obs_msg: the message
        """
        self.context.logger.info(
            "received observation from sender={}".format(obs_msg.sender[-5:])
        )

        strategy = cast(AggregationStrategy, self.context.strategy)
        obs = get_observation_from_message(obs_msg)

        strategy.add_observation(obs_msg.sender, obs)
        strategy.aggregate_observations()

        self.context.logger.info(f"observation: {obs}")

    def _handle_aggregation(self, aggregation_msg: AggregationMessage) -> None:
        """
        Handle the aggregation.

        :param aggregation_msg: the message
        """
        self.context.logger.info(
            "received aggregation from sender={}".format(aggregation_msg.sender[-5:])
        )

    def _handle_invalid(
        self,
        aggregation_msg: AggregationMessage,
        aggregation_dialogue: AggregationDialogue,
    ) -> None:
        """
        Handle a aggregation message of invalid performative.

        :param aggregation_msg: the message
        :param aggregation_dialogue: the dialogue object
        """
        self.context.logger.warning(
            "cannot handle aggregation message of performative={} in dialogue={}.".format(
                aggregation_msg.performative, aggregation_dialogue
            )
        )  # pragma: nocover

    def teardown(self) -> None:
        """Implement the handler teardown."""


class OefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        if oef_search_msg.performative == OefSearchMessage.Performative.SUCCESS:
            self._handle_success(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_success(
        self,
        oef_search_success_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_success_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search success message={} in dialogue={}.".format(
                oef_search_success_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_success_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            description = target_message.service_description
            data_model_name = description.data_model.name
            registration_behaviour = cast(
                SearchBehaviour, self.context.behaviours.search,
            )
            if "location_agent" in data_model_name:
                registration_behaviour.register_service()
            elif "set_service_key" in data_model_name:
                registration_behaviour.register_genus()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "genus"
            ):
                registration_behaviour.register_classification()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "classification"
            ):
                self.context.logger.info(
                    "the agent, with its genus and classification, and its service are successfully registered on the SOEF."
                )
            else:
                self.context.logger.warning(
                    f"received soef SUCCESS message as a reply to the following unexpected message: {target_message}"
                )

    def _handle_error(
        self,
        oef_search_error_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_error_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_error_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_error_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            registration_behaviour = cast(
                SearchBehaviour, self.context.behaviours.search,
            )
            registration_behaviour.failed_registration_msg = target_message

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info(
                f"found no agents in dialogue={oef_search_dialogue}, continue searching."
            )
            return
        strategy = cast(AggregationStrategy, self.context.strategy)
        self.context.logger.info(
            "found agents={}.".format(
                list(map(lambda x: x[-5:], oef_search_msg.agents)),
            )
        )
        strategy.add_peers(oef_search_msg.agents)

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
