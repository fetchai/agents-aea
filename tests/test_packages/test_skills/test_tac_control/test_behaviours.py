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
"""This module contains the tests of the behaviour classes of the tac control skill."""

import datetime
import logging
from pathlib import Path
from typing import cast
from unittest.mock import Mock, PropertyMock, patch

import pytest

from aea.helpers.search.models import Description
from aea.mail.base import Address
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_ADDRESS

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control.behaviours import TacBehaviour
from packages.fetchai.skills.tac_control.dialogues import TacDialogues
from packages.fetchai.skills.tac_control.game import Game, Phase
from packages.fetchai.skills.tac_control.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test tac behaviour of tac_control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.tac_behaviour = cast(TacBehaviour, cls._skill.skill_context.behaviours.tac)
        cls.game = cast(Game, cls._skill.skill_context.game)
        cls.parameters = cast(Parameters, cls._skill.skill_context.parameters)
        cls.tac_dialogues = cast(TacDialogues, cls._skill.skill_context.tac_dialogues)

    def test_init(self):
        """Test the __init__ method of the tac behaviour."""
        assert self.tac_behaviour._registered_description is None

    def test_setup(self):
        """Test the setup method of the tac behaviour."""
        # setup
        mocked_description = Description({"foo1": 1, "bar1": 2})

        # operation
        with patch.object(
            self.game, "get_location_description", return_value=mocked_description
        ):
            with patch.object(self.tac_behaviour.context.logger, "log") as mock_logger:
                self.tac_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(1)

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    def test_act_i(self):
        """Test the act method of the tac behaviour where phase is pre_game and reg_start_time < now < start_time."""
        # setup
        self.game._phase = Phase.PRE_GAME

        mocked_reg_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )
        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )

        self.parameters._registration_start_time = mocked_reg_time
        self.parameters._start_time = mocked_start_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        mocked_description = Description({"foo1": 1, "bar1": 2})

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_register_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(
                    self.tac_behaviour.context.logger, "log"
                ) as mock_logger:
                    self.tac_behaviour.act()

        # after
        assert self.game.phase == Phase.GAME_REGISTRATION

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering TAC data model on SOEF.")
        mock_logger.assert_any_call(
            logging.INFO, f"TAC open for registration until: {mocked_start_time}"
        )

    def test_act_ii(self):
        """Test the act method of the tac behaviour where phase is game_registration and start_time < now < end_time and nb_agent < min_nb_agents"""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        self.parameters._start_time = mocked_start_time
        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(COUNTERPARTY_ADDRESS, "agent_name_1")
        mocked_description = Description({"foo1": 1, "bar1": 2})

        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": "some_agent_name"},
                    True,
                ),
            ),
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(
                    self.tac_behaviour.context.logger, "log"
                ) as mock_logger:
                    self.tac_behaviour.act()

        # after
        self.assert_quantity_in_outbox(2)

        # _cancel_tac
        mock_logger.assert_any_call(
            logging.INFO, "notifying agents that TAC is cancelled."
        )
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.CANCELLED,
            to=COUNTERPARTY_ADDRESS,
            sender=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

        # phase is POST_GAME
        assert self.game.phase == Phase.POST_GAME

        # _unregister_tac
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "unregistering TAC data model from SOEF."
        )

    def test_cancel_tac_not_1_dialogue(self):
        """Test the _cancel_tac method of the tac behaviour where number of dialogues for an agent is 0."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        self.parameters._start_time = mocked_start_time
        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(COUNTERPARTY_ADDRESS, "agent_name_1")
        mocked_description = Description({"foo1": 1, "bar1": 2})

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving dialogue."
                    ):
                        self.tac_behaviour.act()

    def test_cancel_tac_empty_dialogue(self):
        """Test the _cancel_tac method of the tac behaviour where the dialogue is empty."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        self.parameters._start_time = mocked_start_time
        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(COUNTERPARTY_ADDRESS, "agent_name_1")
        mocked_description = Description({"foo1": 1, "bar1": 2})

        dialogue = self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": "some_agent_name"},
                    True,
                ),
            ),
        )
        dialogue._incoming_messages = []

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving last message."
                    ):
                        self.tac_behaviour.act()

    def _assert_tac_message_and_logging_output(
        self, tac_message: TacMessage, participant_address: Address, mocked_logger,
    ):
        has_attributes, error_str = self.message_has_attributes(
            actual_message=tac_message,
            message_type=TacMessage,
            performative=TacMessage.Performative.GAME_DATA,
            to=participant_address,
            sender=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str
        mocked_logger.assert_any_call(
            logging.DEBUG,
            f"sending game data to '{participant_address}': {str(tac_message)}",
        )

    def test_act_iii(self):
        """Test the act method of the tac behaviour where phase is game_registration and start_time < now < end_time and nb_agent < min_nb_agents"""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        self.parameters._start_time = mocked_start_time
        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        agent_1_address = "agent_address_1"
        agent_1_name = "agent_name_1"
        agent_2_address = "agent_address_2"
        agent_2_name = "agent_name_2"

        self.game._registration.register_agent(agent_1_address, agent_1_name)
        self.game._registration.register_agent(agent_2_address, agent_2_name)
        mocked_description = Description({"foo1": 1, "bar1": 2})
        mocked_holdings_summary = "some_holdings_summary"
        mocked_equilibrium_summary = "some_equilibrium_summary"

        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER, {"agent_name": agent_1_name}, True
                ),
            ),
            agent_1_address,
        )
        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER, {"agent_name": agent_2_name}, True
                ),
            ),
            agent_2_address,
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(
                    type(self.game),
                    "holdings_summary",
                    new_callable=PropertyMock,
                    return_value=mocked_holdings_summary,
                ):
                    with patch.object(
                        type(self.game),
                        "equilibrium_summary",
                        new_callable=PropertyMock,
                        return_value=mocked_equilibrium_summary,
                    ):
                        with patch.object(
                            self.tac_behaviour.context.logger, "log"
                        ) as mock_logger:
                            self.tac_behaviour.act()

        # after
        self.assert_quantity_in_outbox(3)

        # _start_tac
        mock_logger.assert_any_call(
            logging.INFO, f"started competition:\n{mocked_holdings_summary}"
        )
        mock_logger.assert_any_call(
            logging.INFO, f"computed equilibrium:\n{mocked_equilibrium_summary}"
        )

        tac_message_1_in_outbox = cast(TacMessage, self.get_message_from_outbox())
        self._assert_tac_message_and_logging_output(
            tac_message_1_in_outbox, agent_1_address, mock_logger
        )

        tac_message_2_in_outbox = cast(TacMessage, self.get_message_from_outbox())
        self._assert_tac_message_and_logging_output(
            tac_message_2_in_outbox, agent_2_address, mock_logger
        )

        # phase is POST_GAME
        assert self.game.phase == Phase.GAME

        # _unregister_tac
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description,
        )
        assert has_attributes, error_str

        assert self.tac_behaviour._registered_description is None

        mock_logger.assert_any_call(
            logging.INFO, "unregistering TAC data model from SOEF."
        )

    def test_start_tac_not_1_dialogue(self):
        """Test the _start_tac method of the tac behaviour where number of dialogues for an agent is 0."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        self.parameters._start_time = mocked_start_time
        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        agent_1_address = "agent_address_1"
        agent_1_name = "agent_name_1"
        agent_2_address = "agent_address_2"
        agent_2_name = "agent_name_2"

        self.game._registration.register_agent(agent_1_address, agent_1_name)
        self.game._registration.register_agent(agent_2_address, agent_2_name)
        mocked_description = Description({"foo1": 1, "bar1": 2})

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving dialogue."
                    ):
                        self.tac_behaviour.act()

    def test_start_tac_empty_dialogue(self):
        """Test the _start_tac method of the tac behaviour where a dialogue is empty.."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_start_time = datetime.datetime.strptime(
            "01 01 2020  00:01", "%d %m %Y %H:%M"
        )
        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )

        self.parameters._start_time = mocked_start_time
        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        agent_1_address = "agent_address_1"
        agent_1_name = "agent_name_1"
        agent_2_address = "agent_address_2"
        agent_2_name = "agent_name_2"

        self.game._registration.register_agent(agent_1_address, agent_1_name)
        self.game._registration.register_agent(agent_2_address, agent_2_name)
        mocked_description = Description({"foo1": 1, "bar1": 2})

        dialogue_1 = self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER, {"agent_name": agent_1_name}, True
                ),
            ),
            agent_1_address,
        )

        dialogue_1._incoming_messages = []

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving last message."
                    ):
                        self.tac_behaviour.act()

    def test_act_iv(self):
        """Test the act method of the tac behaviour where phase is game_registration and start_time < now < end_time and nb_agent < min_nb_agents"""
        # setup
        self.game._phase = Phase.GAME

        mocked_end_time = datetime.datetime.strptime(
            "01 01 2020  00:02", "%d %m %Y %H:%M"
        )
        mocked_now_time = datetime.datetime.strptime(
            "01 01 2020  00:03", "%d %m %Y %H:%M"
        )

        self.parameters._end_time = mocked_end_time

        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        agent_1_address = "agent_address_1"
        agent_1_name = "agent_name_1"
        agent_2_address = "agent_address_2"
        agent_2_name = "agent_name_2"

        self.game._registration.register_agent(agent_1_address, agent_1_name)
        self.game._registration.register_agent(agent_2_address, agent_2_name)
        mocked_description = Description({"foo1": 1, "bar1": 2})
        mocked_holdings_summary = "some_holdings_summary"
        mocked_equilibrium_summary = "some_equilibrium_summary"

        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER, {"agent_name": agent_1_name}, True
                ),
            ),
            agent_1_address,
        )
        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER, {"agent_name": agent_2_name}, True
                ),
            ),
            agent_2_address,
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=mocked_description,
            ):
                with patch.object(
                    type(self.game),
                    "holdings_summary",
                    new_callable=PropertyMock,
                    return_value=mocked_holdings_summary,
                ):
                    with patch.object(
                        type(self.game),
                        "equilibrium_summary",
                        new_callable=PropertyMock,
                        return_value=mocked_equilibrium_summary,
                    ):
                        with patch.object(
                            self.tac_behaviour.context.logger, "log"
                        ) as mock_logger:
                            self.tac_behaviour.act()

        # after
        self.assert_quantity_in_outbox(2)

        # _cancel_tac
        mock_logger.assert_any_call(
            logging.INFO, "notifying agents that TAC is cancelled."
        )
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.CANCELLED,
            to=agent_1_address,
            sender=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.CANCELLED,
            to=agent_2_address,
            sender=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, f"finished competition:\n{mocked_holdings_summary}"
        )
        mock_logger.assert_any_call(
            logging.INFO, f"computed equilibrium:\n{mocked_equilibrium_summary}"
        )

        # phase is POST_GAME
        assert self.game.phase == Phase.POST_GAME
        assert self.skill.skill_context.is_active is False

    def test_teardown(self):
        """Test the teardown method of the service_registration behaviour."""
        # setup
        mocked_description = Description({"foo1": 1, "bar1": 2})
        mocked_location_description = Description({"foo1": 1, "bar1": 2})

        # operation
        with patch.object(
            self.game, "get_unregister_tac_description", return_value=mocked_description
        ):
            with patch.object(
                self.game,
                "get_location_description",
                return_value=mocked_location_description,
            ):
                with patch.object(
                    self.tac_behaviour.context.logger, "log"
                ) as mock_logger:
                    self.tac_behaviour.teardown()

        # after
        self.assert_quantity_in_outbox(2)

        # _unregister_tac
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "unregistering TAC data model from SOEF."
        )

        # _unregister_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_location_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")
