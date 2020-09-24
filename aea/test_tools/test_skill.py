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
"""This module contains test case classes based on pytest for AEA end-to-end testing."""
import copy
import logging
import os
import random
import shutil
import string
import subprocess  # nosec
import sys
import tempfile
import time
from abc import ABC
from contextlib import suppress
from filecmp import dircmp
from io import TextIOWrapper
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union
from unittest import TestCase

import pytest
import yaml

from aea.cli import cli
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE, PackageType
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.configurations.loader import ConfigLoader
from aea.connections.stub.connection import (
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_OUTPUT_FILE_NAME,
)
from aea.exceptions import enforce
from aea.helpers.base import cd, send_control_c, win_popen_kwargs
from aea.mail.base import Envelope
from aea.test_tools.click_testing import CliRunner, Result
from aea.test_tools.constants import DEFAULT_AUTHOR
from aea.test_tools.exceptions import AEATestingException
from aea.test_tools.generic import (
    force_set_config,
    read_envelope_from_file,
    write_envelope_to_file,
)

from tests.conftest import ROOT_DIR


logger = logging.getLogger(__name__)


class BaseSkillTestCase(TestCase):

    path_to_skill: Union[Path, str] = Path(".")
    packages_dir_path: Path = Path("..", "packages")

    @classmethod
    def setup_class(cls) -> None:
        """
        Set up the skill test case.

        - create a dummy agent context

        - load skill from dir
        - make agent context accessible
        """
        pass

    def setup(self) -> None:
        pass

    @classmethod
    def teardown_class(cls):
        # delete the dummy agent
        pass


class SkillBehaviourTestCase(BaseSkillTestCase):

    path_to_skill = Path("packages/fetchai/skills/generic_buyer")

    @mock.patch.object("strategy.is_ledger_tx", return_value="True")
    def test_search_behaviour_setup_is_ledger_tx(self):
        assert outbox._multiplexer.out_queue.qsize == 0
        expected_performative = LedgerApiMessage.Performative.GET_BALANCE
        expected_counterparty = "fetchai/ledger:0.6.0"
        expected_ledger_id = "blah_blah",
        expected_address = "some_address",

        self.context.behaviours.search.setup()

        outbox = self.skill.context.outbox
        assert outbox._multiplexer.out_queue.qsize == 1
        actual_message = outbox._multiplexer.out_queue.get()
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.ledger_id == expected_ledger_id
        assert actual_message.address == expected_address


    @mock.patch.object("strategy.is_ledger_tx", return_value="False")
    def test_search_behaviour_setup_not_is_ledger_tx(self):
        self.context.behaviours.search.setup()
        assert self.context.strategy.is_searching is True

    def test_search_behaviour_act(self):
        pass

    def test_search_behaviour_teardown(self):
        pass


class SkillHandlerTestCase(TestCase):

    path_to_skill = Path("packages/fetchai/skills/generic_buyer")

    def test_fipa_handler_setup(self):
        pass

    def test_fipa_handler_handle(self):
        pass

    def test_fipa_handler_teardown(self):
        pass

    def test_ledger_api_handler_setup(self):
        pass

    def test_ledger_api_handler_handle(self):
        pass

    def test_ledger_api_handler_teardown(self):
        pass

    def test_oef_search_handler_setup(self):
        pass

    def test_oef_search_handler_handle(self):
        pass

    def test_oef_search_handler_teardown(self):
        pass

    def test_signing_handler_setup(self):
        pass

    def test_signing_handler_handle(self):
        pass

    def test_signing_handler_teardown(self):
        pass


class SkillModelTestCase(TestCase):

    path_to_skill = Path("packages/fetchai/skills/generic_buyer")

    def test_strategy(self):
        pass
