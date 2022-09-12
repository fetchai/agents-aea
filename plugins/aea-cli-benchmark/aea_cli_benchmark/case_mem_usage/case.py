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
"""Memory usage check."""
import time
from threading import Thread
from typing import List, Tuple, Union

from aea_cli_benchmark.utils import SyncedGeneratorConnection  # noqa: I100
from aea_cli_benchmark.utils import (
    get_mem_usage_in_mb,
    make_agent,
    make_envelope,
    make_skill,
    wait_for_condition,
)

from aea.protocols.base import Message
from aea.registries.resources import Resources
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage


class TestHandler(Handler):
    """Dummy handler to handle messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Noop setup."""

    def teardown(self) -> None:
        """Noop teardown."""

    def handle(self, message: Message) -> None:
        """Handle incoming message."""
        self.context.outbox.put(make_envelope(message.to, message.sender))


def run(duration: int, runtime_mode: str) -> List[Tuple[str, Union[int, float]]]:
    """Check memory usage."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    connection = SyncedGeneratorConnection.make()
    resources = Resources()
    resources.add_connection(connection)
    agent = make_agent(runtime_mode=runtime_mode, resources=resources)
    agent.resources.add_skill(make_skill(agent, handlers={"test": TestHandler}))

    t = Thread(target=agent.start, daemon=True)
    t.start()
    wait_for_condition(lambda: agent.is_running, timeout=5)

    connection.enable()
    time.sleep(duration)
    connection.disable()
    mem_usage = get_mem_usage_in_mb()
    agent.stop()
    t.join(5)
    rate = connection.count_in / duration

    return [
        ("envelopes received", connection.count_in),
        ("envelopes sent", connection.count_out),
        ("rate (envelopes/second)", rate),
        ("mem usage (Mb)", mem_usage),
    ]
