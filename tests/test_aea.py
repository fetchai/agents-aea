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

"""This module contains the tests for the aea.aea module."""
import os
from threading import Timer, Thread

from aea.aea import AEA
from aea.channels.local.connection import OEFLocalConnection, LocalNode
from aea.mail.base import MailBox
from aea.protocols.base.message import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import AgentContext
from tests.conftest import CUR_PATH


def test_run_aea():
    """Initialize and run an AEA agent."""
    public_key = "mypbk"
    mailbox = MailBox(OEFLocalConnection(public_key, LocalNode()))
    agent = AEA("test_aea", mailbox, directory=os.path.join(CUR_PATH, "data", "dummy_aea"))
    try:
        assert isinstance(agent.context, AgentContext)
        agent.mailbox.connect()

        stopper = Timer(2.0, function=agent.stop)
        stopper.start()
        agent_thread = Thread(target=agent.start)
        agent_thread.start()

        # send proper message
        bytes_msg = DefaultSerializer().encode(Message(type=DefaultMessage.Type.BYTES, content=b"hello"))
        agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="error", message=bytes_msg)

        # send dummy protocol message
        agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="my_dummy_protocol", message=bytes_msg)

        # send wrongly formatted message
        agent.outbox.put_message(to=public_key, sender=public_key, protocol_id="error", message=b"hello")

        stopper.join()
        agent_thread.join()

    finally:
        agent.stop()
