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

"""This package contains a the behaviours."""

import datetime
from typing import Any, Optional, cast

from aea.helpers.search.models import Description
from aea.skills.base import Behaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control.dialogues import (
    OefSearchDialogues,
    TacDialogues,
)
from packages.fetchai.skills.tac_control.game import Game, Phase
from packages.fetchai.skills.tac_control.parameters import Parameters


DEFAULT_MAX_SOEF_REGISTRATION_RETRIES = 5


class TacBehaviour(Behaviour):
    """This class implements the TAC control behaviour."""

    def __init__(self, **kwargs: Any):
        """Instantiate the behaviour."""
        self._max_soef_registration_retries = kwargs.pop(
            "max_soef_registration_retries", DEFAULT_MAX_SOEF_REGISTRATION_RETRIES
        )  # type: int
        super().__init__(**kwargs)
        self._registered_description = None  # type: Optional[Description]
        self.failed_registration_msg = None  # type: Optional[OefSearchMessage]
        self._nb_retries = 0

    def setup(self) -> None:
        """Implement the setup."""
        self._register_agent()

    def act(self) -> None:
        """Implement the act."""
        self._retry_failed_registration()

        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        now = datetime.datetime.now()
        if (
            game.phase.value == Phase.PRE_GAME.value
            and parameters.registration_start_time < now < parameters.start_time
            and game.is_registered_agent
        ):
            game.phase = Phase.GAME_REGISTRATION
            self._register_tac()
            self.context.logger.info(
                "TAC open for registration until: {}".format(parameters.start_time)
            )
        elif (
            game.phase.value == Phase.GAME_REGISTRATION.value
            and parameters.start_time < now < parameters.end_time
        ):
            if game.registration.nb_agents < parameters.min_nb_agents:
                self._cancel_tac(game)
                game.phase = Phase.POST_GAME
                self._unregister_tac()
            else:
                game.phase = Phase.GAME_SETUP
                game.create()
                self._start_tac(game)
                self._unregister_tac()
                game.phase = Phase.GAME
        elif game.phase.value == Phase.GAME.value and now > parameters.end_time:
            self._cancel_tac(game)
            game.phase = Phase.POST_GAME

    def teardown(self) -> None:
        """Implement the task teardown."""
        self._unregister_tac()
        self._unregister_agent()

    def _retry_failed_registration(self) -> None:
        """Retry a failed registration."""
        if self.failed_registration_msg is not None:
            self._nb_retries += 1
            if self._nb_retries > self._max_soef_registration_retries:
                self.context.is_active = False
                return

            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.failed_registration_msg.to,
                performative=self.failed_registration_msg.performative,
                service_description=self.failed_registration_msg.service_description,
            )
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info(
                f"Retrying registration on SOEF. Retry {self._nb_retries} out of {self._max_soef_registration_retries}."
            )

            self.failed_registration_msg = None

    def _register(self, description: Description, logger_msg: str) -> None:
        """
        Register something on the SOEF.

        :param description: the description of what is being registered
        :param logger_msg: the logger message to print after the registration
        """
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info(logger_msg)

    def _register_agent(self) -> None:
        """Register the agent's location."""
        game = cast(Game, self.context.game)
        description = game.get_location_description()
        self._register(description, "registering agent on SOEF.")

    def register_genus(self) -> None:
        """Register the agent's personality genus."""
        game = cast(Game, self.context.game)
        description = game.get_register_personality_description()
        self._register(
            description, "registering agent's personality genus on the SOEF."
        )

    def register_classification(self) -> None:
        """Register the agent's personality classification."""
        game = cast(Game, self.context.game)
        description = game.get_register_classification_description()
        self._register(
            description, "registering agent's personality classification on the SOEF."
        )

    def _register_tac(self) -> None:
        """Register the agent's TAC controller service on the SOEF."""
        game = cast(Game, self.context.game)
        description = game.get_register_tac_description()
        self._register(description, "registering TAC data model on SOEF.")

    def _unregister_tac(self) -> None:
        """Unregister from the OEF as a TAC controller agent."""
        game = cast(Game, self.context.game)
        description = game.get_unregister_tac_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self._registered_description = None
        self.context.logger.info("unregistering TAC data model from SOEF.")

    def _unregister_agent(self) -> None:
        """Unregister agent from the SOEF."""
        game = cast(Game, self.context.game)
        description = game.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering agent from SOEF.")

    def _start_tac(self, game: Game) -> None:
        """
        Create a game and send the game configuration to every registered agent.

        :param game: the game
        """
        count = len(game.conf.agent_addr_to_name)
        participant_names = sorted(list(game.conf.agent_addr_to_name.values()))
        self.context.logger.info(
            f"starting competition with {count} participants and list of participants: {participant_names}"
        )
        self.context.logger.info(
            "started competition:\n{}".format(game.holdings_summary)
        )
        self.context.logger.info(
            "computed equilibrium:\n{}".format(game.equilibrium_summary)
        )
        tac_dialogues = cast(TacDialogues, self.context.tac_dialogues)
        for agent_address in game.conf.agent_addr_to_name.keys():
            _tac_dialogues = tac_dialogues.get_dialogues_with_counterparty(
                agent_address
            )
            if len(_tac_dialogues) != 1:
                raise ValueError("Error when retrieving dialogue.")
            tac_dialogue = _tac_dialogues[0]
            last_msg = tac_dialogue.last_message
            if last_msg is None:
                raise ValueError("Error when retrieving last message.")
            agent_state = game.current_agent_states[agent_address]
            info = (
                {"contract_address": game.conf.contract_address}
                if game.conf.has_contract_address
                else {}
            )
            tac_msg = tac_dialogue.reply(
                performative=TacMessage.Performative.GAME_DATA,
                target_message=last_msg,
                amount_by_currency_id=agent_state.amount_by_currency_id,
                exchange_params_by_currency_id=agent_state.exchange_params_by_currency_id,
                quantities_by_good_id=agent_state.quantities_by_good_id,
                utility_params_by_good_id=agent_state.utility_params_by_good_id,
                fee_by_currency_id=game.conf.fee_by_currency_id,
                currency_id_to_name=game.conf.currency_id_to_name,
                agent_addr_to_name=game.conf.agent_addr_to_name,
                good_id_to_name=game.conf.good_id_to_name,
                version_id=game.conf.version_id,
                info=info,
            )
            self.context.outbox.put_message(message=tac_msg)
            self.context.logger.debug(
                "sending game data to '{}': {}".format(agent_address, str(tac_msg))
            )

    def _cancel_tac(self, game: Game) -> None:
        """
        Notify agents that the TAC is cancelled.

        :param game: the game
        """
        self.context.logger.info("notifying agents that TAC is cancelled.")
        tac_dialogues = cast(TacDialogues, self.context.tac_dialogues)
        for agent_address in game.registration.agent_addr_to_name.keys():
            _tac_dialogues = tac_dialogues.get_dialogues_with_counterparty(
                agent_address
            )
            if len(_tac_dialogues) != 1:
                raise ValueError("Error when retrieving dialogue.")
            tac_dialogue = _tac_dialogues[0]
            last_msg = tac_dialogue.last_message
            if last_msg is None:  # pragma: nocover
                raise ValueError("Error when retrieving last message.")
            tac_msg = tac_dialogue.reply(
                performative=TacMessage.Performative.CANCELLED,
            )
            self.context.outbox.put_message(message=tac_msg)
        if game.phase == Phase.GAME:
            self.context.logger.info(
                "finished competition:\n{}".format(game.holdings_summary)
            )
            self.context.logger.info(
                "computed equilibrium:\n{}".format(game.equilibrium_summary)
            )
            self.context.is_active = False
