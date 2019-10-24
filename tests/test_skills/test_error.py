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
"""The test error skill module contains the tests of the error skill."""
import time
from pathlib import Path
from threading import Thread

from aea.aea import AEA
from aea.connections.local.connection import LocalNode
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.skills.error.behaviours import ErrorBehaviour
from aea.skills.error.tasks import ErrorTask
from ..conftest import CUR_PATH, DummyConnection


class TestSkillError:
    """Test the skill: Error."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        cls.node = LocalNode()
        cls.wallet = Wallet({'default': None})
        cls.agent_name = "Agent0"
        cls.public_key = cls.wallet.public_keys['default']

        cls.connection = DummyConnection()
        cls.mailbox1 = MailBox(cls.connection)
        cls.my_aea = AEA(cls.agent_name, cls.mailbox1, cls.wallet, timeout=2.0, directory=str(Path(CUR_PATH, "data/dummy_aea")))
        cls.t = Thread(target=cls.my_aea.start)
        cls.t.start()
        time.sleep(1.0)

        handlers = cls.my_aea.resources.handler_registry.fetch("default")
        cls.my_error_handler = handlers[1]

    def test_error_handler_handle(self):
        """Test the handle function."""
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=self.public_key,
                            protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.my_error_handler.handle(message=msg, sender=envelope.sender)

    def test_error_teardown(self):
        """Test the teardown function."""
        self.my_error_handler.teardown()

    def test_error_skill_unsupported_protocol(self):
        """Test the unsupported error message."""
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=self.public_key,
                            protocol_id=FIPAMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_unsupported_protocol(envelope)

        envelope = self.connection.out_queue.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") == DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL.value

    def test_error_decoding_error(self):
        """Test the decoding error."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=self.public_key,
                            protocol_id=DefaultMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_decoding_error(envelope)

        envelope = self.connection.out_queue.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") == DefaultMessage.ErrorCode.DECODING_ERROR.value

    def test_error_invalid_message(self):
        """Test the invalid message."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=self.public_key,
                            protocol_id=OEFMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_invalid_message(envelope)

        envelope = self.connection.out_queue.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") < DefaultMessage.ErrorCode.INVALID_MESSAGE.value

    def test_error_unsupported_skill(self):
        """Test the unsupported skill."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.public_key, sender=self.public_key,
                            protocol_id=DefaultMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_unsupported_skill(envelope=envelope)

        envelope = self.connection.out_queue.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") < DefaultMessage.ErrorCode.UNSUPPORTED_SKILL.value


    @classmethod
    def teardown(cls):
        """Teardown method."""
        cls.my_aea.stop()
        cls.t.join()

