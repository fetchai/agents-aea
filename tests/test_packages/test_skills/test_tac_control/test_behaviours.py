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
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

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

        cls.mocked_reg_time = cls._time("00:02")
        cls.mocked_start_time = cls._time("00:04")
        cls.mocked_end_time = cls._time("00:06")

        cls.parameters._registration_start_time = cls.mocked_reg_time
        cls.parameters._start_time = cls.mocked_start_time
        cls.parameters._end_time = cls.mocked_end_time

        cls.mocked_description = Description({"foo1": 1, "bar1": 2})

        cls.agent_1_address = "agent_address_1"
        cls.agent_1_name = "agent_name_1"
        cls.agent_2_address = "agent_address_2"
        cls.agent_2_name = "agent_name_2"

        cls.registration_message = OefSearchMessage(
            dialogue_reference=("", ""),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description="some_service_description",
        )
        cls.registration_message.sender = str(cls._skill.skill_context.skill_id)
        cls.registration_message.to = cls._skill.skill_context.search_service_address

    def test_init(self):
        """Test the __init__ method of the tac behaviour."""
        assert self.tac_behaviour._registered_description is None

    def test_setup(self):
        """Test the setup method of the tac behaviour."""
        # operation
        with patch.object(
            self.game, "get_location_description", return_value=self.mocked_description
        ):
            with patch.object(self.tac_behaviour.context.logger, "log") as mock_logger:
                self.tac_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(1)

        # _register_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    @staticmethod
    def _time(time: str):
        date_time = "01 01 2020  " + time
        return datetime.datetime.strptime(date_time, "%d %m %Y %H:%M")

    def test_act_i(self):
        """Test the act method of the tac behaviour where phase is pre_game and reg_start_time < now < start_time."""
        # setup
        self.game._phase = Phase.PRE_GAME
        self.game.is_registered_agent = True

        mocked_now_time = self._time("00:03")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_register_tac_description",
                return_value=self.mocked_description,
            ):
                with patch.object(
                    self.tac_behaviour.context.logger, "log"
                ) as mock_logger:
                    self.tac_behaviour.act()

        # after
        # act
        assert self.game.phase == Phase.GAME_REGISTRATION

        # _register_tac
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "registering TAC data model on SOEF.")

        # act
        mock_logger.assert_any_call(
            logging.INFO, f"TAC open for registration until: {self.mocked_start_time}"
        )

    def test_act_ii(self):
        """Test the act method of the tac behaviour where phase is game_registration and start_time < now < end_time and nb_agent < min_nb_agents."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now_time = self._time("00:05")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(
            COUNTERPARTY_AGENT_ADDRESS, self.agent_1_name
        )

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
                return_value=self.mocked_description,
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
            to=COUNTERPARTY_AGENT_ADDRESS,
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
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "unregistering TAC data model from SOEF."
        )

    def test_cancel_tac_not_1_dialogue(self):
        """Test the _cancel_tac method of the tac behaviour where number of dialogues for an agent is 0."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now_time = self._time("00:05")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(
            COUNTERPARTY_AGENT_ADDRESS, self.agent_1_name
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=self.mocked_description,
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

        mocked_now_time = self._time("00:05")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(
            self.skill.skill_context.agent_address, self.agent_1_name
        )

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
                return_value=self.mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving dialogue."
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
        """Test the act method of the tac behaviour where phase is game_registration and start_time < now < end_time and nb_agent >= min_nb_agents"""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now_time = self._time("00:05")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2

        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)
        mocked_holdings_summary = "some_holdings_summary"
        mocked_equilibrium_summary = "some_equilibrium_summary"

        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": self.agent_1_name},
                    True,
                ),
            ),
            self.agent_1_address,
        )
        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": self.agent_2_name},
                    True,
                ),
            ),
            self.agent_2_address,
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=self.mocked_description,
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
            tac_message_1_in_outbox, self.agent_1_address, mock_logger
        )

        tac_message_2_in_outbox = cast(TacMessage, self.get_message_from_outbox())
        self._assert_tac_message_and_logging_output(
            tac_message_2_in_outbox, self.agent_2_address, mock_logger
        )

        # phase is POST_GAME
        assert self.game.phase == Phase.GAME

        # _unregister_tac
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str

        assert self.tac_behaviour._registered_description is None

        mock_logger.assert_any_call(
            logging.INFO, "unregistering TAC data model from SOEF."
        )

    def test_register_genus(self):
        """Test the register_genus method of the service_registration behaviour."""
        # operation
        with patch.object(
            self.game,
            "get_register_personality_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.tac_behaviour.context.logger, "log") as mock_logger:
                self.tac_behaviour.register_genus()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality genus on the SOEF."
        )

    def test_register_classification(self):
        """Test the register_classification method of the service_registration behaviour."""
        # operation
        with patch.object(
            self.game,
            "get_register_classification_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.tac_behaviour.context.logger, "log") as mock_logger:
                self.tac_behaviour.register_classification()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality classification on the SOEF."
        )

    def test_start_tac_not_1_dialogue(self):
        """Test the _start_tac method of the tac behaviour where number of dialogues for an agent is 0."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now_time = self._time("00:05")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=self.mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving dialogue."
                    ):
                        self.tac_behaviour.act()

    def test_start_tac_empty_dialogue(self):
        """Test the _start_tac method of the tac behaviour where a dialogue is empty."""
        # setup
        self.game._phase = Phase.GAME_REGISTRATION

        mocked_now_time = self._time("00:05")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        dialogue_1 = self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": self.agent_1_name},
                    True,
                ),
            ),
            self.agent_1_address,
        )

        dialogue_1._incoming_messages = []

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=self.mocked_description,
            ):
                with patch.object(self.tac_behaviour.context.logger, "log"):
                    with pytest.raises(
                        ValueError, match="Error when retrieving last message."
                    ):
                        self.tac_behaviour.act()

    def test_act_iv(self):
        """Test the act method of the tac behaviour where phase is GAME and end_time < now."""
        # setup
        self.game._phase = Phase.GAME

        mocked_now_time = self._time("00:07")
        datetime_mock = Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mocked_now_time

        self.parameters._min_nb_agents = 2
        self.game._registration.register_agent(self.agent_1_address, self.agent_1_name)
        self.game._registration.register_agent(self.agent_2_address, self.agent_2_name)

        mocked_holdings_summary = "some_holdings_summary"
        mocked_equilibrium_summary = "some_equilibrium_summary"

        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": self.agent_1_name},
                    True,
                ),
            ),
            self.agent_1_address,
        )
        self.prepare_skill_dialogue(
            self.tac_dialogues,
            (
                DialogueMessage(
                    TacMessage.Performative.REGISTER,
                    {"agent_name": self.agent_2_name},
                    True,
                ),
            ),
            self.agent_2_address,
        )

        # operation
        with patch("datetime.datetime", new=datetime_mock):
            with patch.object(
                self.game,
                "get_unregister_tac_description",
                return_value=self.mocked_description,
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
            to=self.agent_1_address,
            sender=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=TacMessage,
            performative=TacMessage.Performative.CANCELLED,
            to=self.agent_2_address,
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

    def test_act_v(self):
        """Test the act method of the tac behaviour where failed_registration_msg is NOT None."""
        # setup
        self.tac_behaviour.failed_registration_msg = self.registration_message

        with patch.object(self.tac_behaviour.context.logger, "log") as mock_logger:
            self.tac_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _retry_failed_registration
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=type(self.registration_message),
            performative=self.registration_message.performative,
            to=self.registration_message.to,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.registration_message.service_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"Retrying registration on SOEF. Retry {self.tac_behaviour._nb_retries} out of {self.tac_behaviour._max_soef_registration_retries}.",
        )
        assert self.tac_behaviour.failed_registration_msg is None

    def test_act_vi(self):
        """Test the act method of the tac behaviour where failed_registration_msg is NOT None and max retries is reached."""
        # setup
        self.tac_behaviour.failed_registration_msg = self.registration_message
        self.tac_behaviour._max_soef_registration_retries = 2
        self.tac_behaviour._nb_retries = 2

        self.tac_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.skill.skill_context.is_active is False

    def test_teardown(self):
        """Test the teardown method of the service_registration behaviour."""
        # setup
        mocked_location_description = Description({"foo1": 1, "bar1": 2})

        # operation
        with patch.object(
            self.game,
            "get_unregister_tac_description",
            return_value=self.mocked_description,
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
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
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
            sender=str(self.skill.skill_context.skill_id),
            service_description=mocked_location_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")
