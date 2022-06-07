# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Envelopes generation speed for Behaviour act test."""
import time
from threading import Thread
from typing import List, Tuple, Union, cast

from aea_cli_benchmark.utils import SyncedGeneratorConnection  # noqa: I100
from aea_cli_benchmark.utils import (
    make_agent,
    make_envelope,
    make_skill,
    wait_for_condition,
)

from aea.registries.resources import Resources
from aea.skills.base import Behaviour

from packages.fetchai.protocols.default.message import DefaultMessage


class TestBehaviour(Behaviour):
    """Dummy handler to handle messages."""

    _tick_interval = 1

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Set up behaviour."""
        self.count = 0  # pylint: disable=attribute-defined-outside-init

    def teardown(self) -> None:
        """Tear up behaviour."""

    def act(self) -> None:
        """Perform action on periodic basis."""
        s = time.time()
        while time.time() - s < self.tick_interval:
            self.context.outbox.put(make_envelope("1", "2"))
            self.count += 1


def run(duration: int, runtime_mode: str) -> List[Tuple[str, Union[int, float]]]:
    """Test act message generate performance."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    resources = Resources()
    connection = SyncedGeneratorConnection.make()
    resources.add_connection(connection)
    agent = make_agent(runtime_mode=runtime_mode, resources=resources)
    skill = make_skill(agent, behaviours={"test": TestBehaviour})
    agent.resources.add_skill(skill)
    t = Thread(target=agent.start, daemon=True)
    t.start()
    wait_for_condition(lambda: agent.is_running, timeout=5)
    time.sleep(duration)
    agent.stop()
    t.join(5)

    rate = connection.count_in / duration
    return [
        ("envelopes sent", cast(TestBehaviour, skill.behaviours["test"]).count),
        ("envelopes received", connection.count_in),
        ("rate(envelopes/second)", rate),
    ]
