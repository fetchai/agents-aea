# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Base classes for p2p_libp2p tests"""

import atexit
import logging
import os
from pathlib import Path
from typing import List

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import TEMP_LIBP2P_TEST_DIR, remove_test_directory


class BaseP2PLibp2pTest:
    """Base class for ACN p2p libp2p tests"""

    cwd: str
    t: str
    tmp_dir: str
    tmp_client_dir: str
    log_files: List[str] = []
    multiplexers: List[Multiplexer] = []
    capture_log = True

    @classmethod
    def setup_class(cls):
        """Set the test up"""

        atexit.register(cls.teardown_class)
        cls.cwd, cls.t = os.getcwd(), TEMP_LIBP2P_TEST_DIR
        if Path(cls.t).exists():
            cls.remove_temp_test_dir()
        cls.tmp_dir = os.path.join(cls.t, "temp_dir")
        cls.tmp_client_dir = os.path.join(cls.t, "temp_client_dir")
        Path(cls.tmp_dir).mkdir(parents=True, exist_ok=True)
        os.chdir(cls.t)

    @classmethod
    def teardown_class(cls):
        """Tear down the test"""

        logging.debug(f"Cleaning up {cls.__name__}")
        for mux in cls.multiplexers:
            for con in mux.connections:
                con.disconnect()
            mux.disconnect()
        cls.multiplexers.clear()
        cls.log_files.clear()
        os.chdir(cls.cwd)
        if Path(cls.t).exists():
            cls.remove_temp_test_dir()
        logging.debug(f"Teardown of {cls.__name__} completed")

    @classmethod
    def remove_temp_test_dir(cls) -> None:
        """Attempt to remove the temporary directory used during tests"""
        success = remove_test_directory(cls.t)
        if not success:
            logging.debug(f"{cls.t} could NOT be deleted")

    def enveloped_default_message(self, to: str, sender: str) -> Envelope:
        """Generate a enveloped default message for tests"""

        message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )

        envelope = Envelope(
            to=to,
            sender=sender,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=message,
        )

        return envelope

    @property
    def all_multiplexer_connections_connected(self) -> bool:
        """Check if all connection of all multiplexers are connected"""

        return all(c.is_connected for mux in self.multiplexers for c in mux.connections)

    def sent_is_delivered_envelope(self, sent: Envelope, delivered: Envelope) -> bool:
        """Check if attributes on sent match those on delivered envelope"""

        attrs = ["to", "sender", "protocol_specification_id", "message_bytes"]
        return all(getattr(sent, attr) == getattr(delivered, attr) for attr in attrs)
