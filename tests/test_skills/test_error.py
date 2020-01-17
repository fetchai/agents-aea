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

import os
import time
from pathlib import Path
from threading import Thread

from aea.aea import AEA
from aea.crypto.default import DEFAULT
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.registries.base import Resources
from aea.skills.base import SkillContext
from aea.skills.error.behaviours import ErrorBehaviour
from aea.skills.error.handlers import ErrorHandler
from aea.skills.error.tasks import ErrorTask

from packages.fetchai.connections.local.connection import LocalNode
from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.protocols.oef.message import OEFMessage

from ..conftest import CUR_PATH, DummyConnection


class TestSkillError:
    """Test the skill: Error."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        cls.node = LocalNode()
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        cls.wallet = Wallet({"default": private_key_pem_path})
        cls.ledger_apis = LedgerApis({}, DEFAULT)
        cls.agent_name = "Agent0"
        cls.address = cls.wallet.addresses["default"]

        cls.connection = DummyConnection()
        cls.connections = [cls.connection]
        cls.my_aea = AEA(
            cls.agent_name,
            cls.connections,
            cls.wallet,
            cls.ledger_apis,
            timeout=2.0,
            resources=Resources(str(Path(CUR_PATH, "data/dummy_aea"))),
            programmatic=False,
        )
        cls.t = Thread(target=cls.my_aea.start)
        cls.t.start()
        time.sleep(0.5)

        cls.skill_context = SkillContext(cls.my_aea._context)
        cls.my_error_handler = ErrorHandler(skill_context=cls.skill_context)

    def test_error_handler_handle(self):
        """Test the handle function."""
        msg = FIPAMessage(
            message_id=0,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FIPAMessage.Performative.ACCEPT,
        )
        msg.counterparty = "a_counterparty"
        self.my_error_handler.handle(message=msg)

    def test_error_skill_unsupported_protocol(self):
        """Test the unsupported error message."""
        msg = FIPAMessage(
            message_id=0,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FIPAMessage.Performative.ACCEPT,
        )
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=self.address,
            protocol_id=FIPAMessage.protocol_id,
            message=msg_bytes,
        )

        self.my_error_handler.send_unsupported_protocol(envelope)

        envelope = self.my_aea.inbox.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.type == DefaultMessage.Type.ERROR
        assert msg.error_code == DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL

    def test_error_decoding_error(self):
        """Test the decoding error."""
        msg = FIPAMessage(
            message_id=0,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FIPAMessage.Performative.ACCEPT,
        )
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=self.address,
            protocol_id=DefaultMessage.protocol_id,
            message=msg_bytes,
        )

        self.my_error_handler.send_decoding_error(envelope)

        envelope = self.my_aea.inbox.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") == DefaultMessage.ErrorCode.DECODING_ERROR.value

    def test_error_invalid_message(self):
        """Test the invalid message."""
        msg = FIPAMessage(
            message_id=0,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FIPAMessage.Performative.ACCEPT,
        )
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=self.address,
            protocol_id=OEFMessage.protocol_id,
            message=msg_bytes,
        )

        self.my_error_handler.send_invalid_message(envelope)

        envelope = self.my_aea.inbox.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") == DefaultMessage.ErrorCode.INVALID_MESSAGE.value

    def test_error_unsupported_skill(self):
        """Test the unsupported skill."""
        msg = FIPAMessage(
            message_id=0,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FIPAMessage.Performative.ACCEPT,
        )
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to=self.address,
            sender=self.address,
            protocol_id=DefaultMessage.protocol_id,
            message=msg_bytes,
        )

        self.my_error_handler.send_unsupported_skill(envelope=envelope)

        envelope = self.my_aea.inbox.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert msg.get("type") == DefaultMessage.Type.ERROR
        assert msg.get("error_code") == DefaultMessage.ErrorCode.UNSUPPORTED_SKILL.value

    def test_error_behaviour_instantiation(self):
        """Test that we can instantiate the 'ErrorBehaviour' class."""
        ErrorBehaviour(skill_context=self.skill_context)

    def test_error_task_instantiation(self):
        """Test that we can instantiate the 'ErrorTask' class."""
        ErrorTask(skill_context=self.skill_context)

    @classmethod
    def teardown_class(cls):
        """Teardown method."""
        cls.my_aea.stop()
        cls.t.join()
