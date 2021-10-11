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

import logging
import os
import unittest.mock
from threading import Thread
from unittest.mock import MagicMock

from aea.aea import AEA
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import InBox, Multiplexer
from aea.registries.resources import Resources
from aea.skills.base import SkillContext

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.skills.error.handlers import ErrorHandler

from tests.common.utils import wait_for_condition
from tests.conftest import CUR_PATH, _make_dummy_connection


logger = logging.getLogger(__file__)


class InboxWithHistory(InBox):
    """Inbox with history of all messages every fetched."""

    def __init__(self, multiplexer: Multiplexer):
        """Inin inbox."""
        super().__init__(multiplexer)
        self._history = []  # type: ignore

    def get(self, *args, **kwargs) -> Envelope:
        """Get envelope."""
        item = super().get(*args, **kwargs)
        self._history.append(item)
        return item

    async def async_get(self, *args, **kwargs) -> Envelope:
        """Get envelope."""
        item = await super().async_get()
        self._history.append(item)
        return item


class TestSkillError:
    """Test the skill: Error."""

    def setup(self):
        """Test the initialisation of the AEA."""
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        self.wallet = Wallet({DEFAULT_LEDGER: private_key_path})
        self.agent_name = "Agent0"
        self.data_dir = MagicMock()

        self.connection = _make_dummy_connection()
        self.identity = Identity(
            self.agent_name,
            address=self.wallet.addresses[DEFAULT_LEDGER],
            public_key=self.wallet.public_keys[DEFAULT_LEDGER],
        )
        self.address = self.identity.address
        resources = Resources()
        resources.add_connection(self.connection)
        self.my_aea = AEA(
            self.identity,
            self.wallet,
            resources=resources,
            data_dir=self.data_dir,
            period=0.1,
            default_connection=self.connection.public_id,
        )

        self.my_aea._inbox = InboxWithHistory(self.my_aea.runtime.multiplexer)
        self.skill_context = SkillContext(self.my_aea._context)
        logger_name = "aea.{}.skills.{}.{}".format(
            self.my_aea._context.agent_name, "fetchai", "error"
        )
        self.skill_context._logger = logging.getLogger(logger_name)
        self.my_error_handler = ErrorHandler(
            name="error", skill_context=self.skill_context
        )
        self.t = Thread(target=self.my_aea.start)
        self.t.start()
        wait_for_condition(
            lambda: self.my_aea.runtime and self.my_aea.runtime.is_running, 10
        )

    def test_error_handler_handle(self):
        """Test the handle function."""
        msg = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        msg.to = "a_counterparty"
        self.my_error_handler.handle(message=msg)

    def test_error_skill_unsupported_protocol(self):
        """Test the unsupported error message."""
        self.my_aea._inbox._history = []
        msg = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        msg.to = self.address
        envelope = Envelope(to=msg.to, sender=self.address, message=msg,)

        self.my_error_handler.send_unsupported_protocol(envelope)

        wait_for_condition(lambda: len(self.my_aea._inbox._history) >= 1, timeout=5)
        envelope = self.my_aea._inbox._history[-1]
        msg = envelope.message
        assert msg.performative == DefaultMessage.Performative.ERROR
        assert msg.error_code == DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL

    def test_error_decoding_error(self):
        """Test the decoding error."""
        self.my_aea._inbox._history = []
        msg = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        msg.to = self.address
        envelope = Envelope(to=msg.to, sender=self.address, message=msg,)

        self.my_error_handler.send_decoding_error(envelope)
        wait_for_condition(lambda: len(self.my_aea._inbox._history) >= 1, timeout=5)
        envelope = self.my_aea._inbox._history[-1]

        msg = envelope.message
        assert msg.performative == DefaultMessage.Performative.ERROR
        assert msg.error_code == DefaultMessage.ErrorCode.DECODING_ERROR

    def test_error_unsupported_skill(self):
        """Test the unsupported skill."""
        msg = FipaMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=FipaMessage.Performative.ACCEPT,
        )
        msg.to = self.address
        msg.sender = self.address
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)

        self.my_error_handler.send_unsupported_skill(envelope=envelope)

        wait_for_condition(lambda: len(self.my_aea._inbox._history) >= 1, timeout=5)
        envelope = self.my_aea._inbox._history[-1]

        msg = envelope.message
        assert msg.performative == DefaultMessage.Performative.ERROR
        assert msg.error_code == DefaultMessage.ErrorCode.UNSUPPORTED_SKILL

    def test_error_unsupported_skill_when_skill_id_is_none(self):
        """Test the 'send_unsupported_skill' when the skill id in the envelope is None."""
        protocol_id = PublicId.from_str("author/name:0.1.0")
        envelope = Envelope(
            to="", sender="", protocol_specification_id=protocol_id, message=b"",
        )
        with unittest.mock.patch.object(self.skill_context.outbox, "put_message"):
            with unittest.mock.patch.object(
                self.skill_context._logger, "warning"
            ) as mock_logger_warning:
                self.my_error_handler.send_unsupported_skill(envelope)
                mock_logger_warning.assert_called_with(
                    f"Cannot handle envelope: no active handler registered for the protocol_specification_id='{protocol_id}'."
                )

    def teardown(self):
        """Teardown method."""
        self.my_aea.stop()
        self.t.join()
