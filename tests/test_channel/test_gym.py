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

"""This test module contains the tests for the Gym channel and connection."""

import time
from typing import Any, Tuple

from aea.channels.gym.gym import GymConnection, DEFAULT_GYM
from aea.mail.base import Envelope, MailBox
from aea.protocols.gym.message import GymMessage
from aea.protocols.gym.serialization import GymSerializer


Action = Any
Observation = Any
Reward = Any
Done = bool
Info = Any
Feedback = Tuple[Observation, Reward, Done, Info]


class GymEnvStub:
    """Stubs a Gym Env."""

    def step(self, action: Action) -> Feedback:
        """Take a step."""
        return None, 1, False, {}


def test_connection():
    """Test that two mailbox can connect to the node."""
    mailbox = MailBox(GymConnection("agent_public_key", GymEnvStub()))

    mailbox.connect()

    mailbox.disconnect()


def test_communication():
    """Test that the gym can be communicated with."""
    mailbox = MailBox(GymConnection("agent_public_key", GymEnvStub()))

    mailbox.connect()

    msg = GymMessage(performative=GymMessage.Performative.ACT, action='some_action', step_id=1)
    msg_bytes = GymSerializer().encode(msg)
    envelope = Envelope(to=DEFAULT_GYM, sender="agent_public_key", protocol_id=GymMessage.protocol_id, message=msg_bytes)
    mailbox.send(envelope)

    time.sleep(1.0)

    envelope = mailbox.inbox.get(block=True, timeout=1.0)
    assert envelope.sender == DEFAULT_GYM
    assert envelope.to == "agent_public_key"
    msg = GymSerializer().decode(envelope.message)
    assert envelope.protocol_id == "gym"
    assert msg.get("observation") is None
    assert msg.get("reward") == 1
    assert msg.get("done") is False
    assert msg.get("info") == {}
    assert msg.get("step_id") == 1

    mailbox.disconnect()
