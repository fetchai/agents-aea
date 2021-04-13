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
"""This module contains the tests of the strategy class of the tac negotiation skill."""

from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.crypto.ledger_apis import LedgerApis
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.registration_aw1.behaviours import AW1RegistrationBehaviour
from packages.fetchai.skills.registration_aw1.dialogues import (
    RegisterDialogues,
    SigningDialogues,
)
from packages.fetchai.skills.registration_aw1.handlers import (
    AW1RegistrationHandler,
    SigningHandler,
)
from packages.fetchai.skills.registration_aw1.strategy import Strategy

from tests.conftest import ROOT_DIR


class RegiatrationAW1TestCase(BaseSkillTestCase):
    """Sets the registration_aw1 class up for testing (overrides the necessary config values so tests can be done on registration_aw1 skill)."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "registration_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.developer_handle = "some_developer_handle"
        cls.ethereum_address = "some_ethereum_address"
        cls.signature_of_fetchai_address = "some_signature_of_fetchai_address"
        cls.shared_storage_key = "some_shared_storage_key"
        cls.tweet = "some_tweet"

        cls.aw1_registration_aea = "aw1_registration_aea_1"
        cls.aw1_registration_aeas = {cls.aw1_registration_aea}
        cls.whitelist = [cls.aw1_registration_aea]
        config_overrides = {
            "models": {
                "strategy": {
                    "args": {
                        "developer_handle": cls.developer_handle,
                        "ethereum_address": cls.ethereum_address,
                        "signature_of_fetchai_address": cls.signature_of_fetchai_address,
                        "shared_storage_key": cls.shared_storage_key,
                        "whitelist": cls.whitelist,
                        "tweet": cls.tweet,
                    }
                }
            },
        }

        with patch.object(LedgerApis, "is_valid_address", return_value=True):
            super().setup(
                config_overrides=config_overrides,
                shared_state={cls.shared_storage_key: None},
            )

        cls.register_behaviour = cast(
            AW1RegistrationBehaviour, cls._skill.skill_context.behaviours.registration,
        )
        cls.register_handler = cast(
            AW1RegistrationHandler, cls._skill.skill_context.handlers.registration
        )
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )

        cls.register_dialogues = cast(
            RegisterDialogues, cls._skill.skill_context.register_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )

        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger
