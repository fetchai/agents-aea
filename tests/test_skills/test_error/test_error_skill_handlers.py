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
"""This module contains the tests for aea.aea.py."""

import time
from pathlib import Path
from threading import Thread

from aea.aea import AEA
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox, Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.skills.base import SkillContext
from tests.conftest import CUR_PATH

from aea.skills.error.handlers import ErrorHandler


class TestSkillError:
    """Test the skill: Error."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        cls.node = LocalNode()
        cls.wallet = Wallet({'default': None})
        cls.mailbox1 = MailBox(OEFLocalConnection(cls.wallet.public_keys['default'], cls.node))
        cls.my_aea = AEA("Agent0", cls.mailbox1, cls.wallet, directory=str(Path(CUR_PATH, "data/dummy_aea")))

        cls.skill_context = SkillContext(cls.my_aea.context)
        cls.my_error_handler = ErrorHandler(skill_context=cls.skill_context)

    def test_error_handler_setup(self):
        """Test the setup."""
        self.my_error_handler.setup()

    def test_error_handler_handle(self):
        """Test the handle function."""
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.wallet.public_keys['default'], sender="test_mail",
                            protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.my_error_handler.handle(message=msg, sender=envelope.sender)

    def test_error_teardown(self):
        """Test the teardown function."""
        self.my_error_handler.teardown()

    def test_error_skill_unsupported_protocol(self):
        """Test the unsupported error message."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.wallet.public_keys['default'], sender="test_mail",
                            protocol_id=FIPAMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_unsupported_protocol(envelope)

        try:
            t.start()
            time.sleep(0.1)
            envelope = self.my_aea.outbox._queue.get(block=True, timeout=0.1)
            msg = DefaultSerializer().decode(envelope.message)
            assert msg.get("type") == DefaultMessage.Type.ERROR
            assert msg.get("error_code") == DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL.value

        finally:
            self.my_aea.stop()
            t.join()

    def test_error_decoding_error(self):
        """Test the decoding error."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.wallet.public_keys['default'], sender="test_mail",
                            protocol_id=DefaultMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_decoding_error(envelope)

        try:
            t.start()
            time.sleep(0.1)
            envelope = self.my_aea.outbox._queue.get(block=True, timeout=0.1)
            msg = DefaultSerializer().decode(envelope.message)
            assert msg.get("type") == DefaultMessage.Type.ERROR
            assert msg.get("error_code") < -1000

        finally:
            self.my_aea.stop()
            t.join()

    def test_error_invalid_message(self):
        """Test the invalid message."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.wallet.public_keys['default'], sender="test_mail",
                            protocol_id=OEFMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_invalid_message(envelope)

        try:
            t.start()
            time.sleep(0.1)
            envelope = self.my_aea.outbox._queue.get(block=True, timeout=0.1)
            msg = DefaultSerializer().decode(envelope.message)
            assert msg.get("type") == DefaultMessage.Type.ERROR
            assert msg.get("error_code") < -1000

        finally:
            self.my_aea.stop()
            t.join()

    def test_error_unsupported_skill(self):
        """Test the unsupported skill."""
        t = Thread(target=self.my_aea.start)
        msg = FIPAMessage(message_id=0, dialogue_id=0, target=0, performative=FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to=self.wallet.public_keys['default'], sender="test_mail",
                            protocol_id=DefaultMessage.protocol_id, message=msg_bytes)

        self.my_error_handler.send_unsupported_skill(envelope=envelope)

        try:
            t.start()
            time.sleep(0.1)
            envelope = self.my_aea.outbox._queue.get(block=True, timeout=0.1)
            msg = DefaultSerializer().decode(envelope.message)
            assert msg.get("type") == DefaultMessage.Type.ERROR
            assert msg.get("error_code") < -1000

        finally:
            self.my_aea.stop()
            t.join()


    @classmethod
    def teardown(cls):
        pass
