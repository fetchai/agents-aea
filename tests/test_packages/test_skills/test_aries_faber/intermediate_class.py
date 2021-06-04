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
"""This module sets up test environment for aries_faber skill."""

import json
from pathlib import Path
from typing import cast

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Query,
)
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.behaviours import FaberBehaviour
from packages.fetchai.skills.aries_faber.dialogues import (
    DefaultDialogues,
    HttpDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_faber.handlers import HttpHandler, OefSearchHandler
from packages.fetchai.skills.aries_faber.strategy import Strategy

from tests.conftest import ROOT_DIR


class AriesFaberTestCase(BaseSkillTestCase):
    """Sets the aries_faber class up for testing."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "aries_faber")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.location = {"longitude": 0.1270, "latitude": 51.5194}
        cls.search_query = {
            "search_key": "intro_service",
            "search_value": "intro_alice",
            "constraint_type": "==",
        }
        cls.search_radius = 5.0
        cls.admin_host = "127.0.0.1"
        cls.admin_port = 8021
        cls.ledger_url = "http://127.0.0.1:9000"
        config_overrides = {
            "models": {
                "strategy": {
                    "args": {
                        "location": cls.location,
                        "search_query": cls.search_query,
                        "search_radius": cls.search_radius,
                        "admin_host": cls.admin_host,
                        "admin_port": cls.admin_port,
                        "ledger_url": cls.ledger_url,
                    }
                }
            },
        }

        super().setup(config_overrides=config_overrides)

        # behaviours
        cls.faber_behaviour = cast(
            FaberBehaviour, cls._skill.skill_context.behaviours.faber,
        )

        # dialogues
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )
        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )

        # handlers
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef_search
        )

        # models
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

        cls.logger = cls._skill.skill_context.logger

        # mocked objects
        cls.mocked_method = "SOME_METHOD"
        cls.mocked_url = "www.some-url.com"
        cls.mocked_version = "some_version"
        cls.mocked_headers = "some_headers"
        cls.body_dict = {"some_key": "some_value"}
        cls.body_str = "some_body"
        cls.body_bytes = b"some_body"
        cls.mocked_body_bytes = json.dumps(cls.body_str).encode("utf-8")
        cls.mocked_query = Query(
            [Constraint("some_attribute_name", ConstraintType("==", "some_value"))],
            DataModel(
                "some_data_model_name",
                [
                    Attribute(
                        "some_attribute_name",
                        str,
                        False,
                        "Some attribute descriptions.",
                    )
                ],
            ),
        )
        cls.mocked_proposal = Description(
            {
                "contract_address": "some_contract_address",
                "token_id": "123456",
                "trade_nonce": "876438756348568",
                "from_supply": "543",
                "to_supply": "432",
                "value": "67",
            }
        )

        # list of messages
        cls.list_of_http_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": cls.mocked_method,
                    "url": cls.mocked_url,
                    "headers": cls.mocked_headers,
                    "version": cls.mocked_version,
                    "body": cls.mocked_body_bytes,
                },
                is_incoming=False,
            ),
        )

        cls.list_of_oef_search_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES,
                {"query": cls.mocked_query},
            ),
        )
