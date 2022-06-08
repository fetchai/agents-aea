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

"""End-to-end test for AEA connecting using HTTP Client connection, to an Aries Cloud Agent."""

import asyncio
import logging
import os
import shutil
import subprocess  # nosec
import time
from threading import Thread
from typing import Optional
from unittest.mock import MagicMock

import pytest
import yaml

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import (
    ConnectionConfig,
    ProtocolConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message, Protocol
from aea.registries.resources import Resources
from aea.skills.base import Handler, Skill, SkillContext

from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.protocols.http.message import HttpMessage


logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestAEAToACA:
    """End-to-end test for an AEA connecting to an ACA via the http client connection."""

    @classmethod
    def setup_class(cls):
        """Initialise the class."""
        cls.aca_admin_address = "127.0.0.1"
        cls.aca_admin_port = 8020

        cls.aea_address = "some string"
        cls.aea_public_key = "some public_key"
        cls.aea_identity = Identity(
            "identity", address=cls.aea_address, public_key=cls.aea_public_key
        )

        cls.cwd = os.getcwd()

        # check Aries Cloud Agents (ACA) is installed
        res = shutil.which("aca-py")
        if res is None:
            pytest.skip(
                "Please install Aries Cloud Agents first! See the following link: https://github.com/hyperledger/aries-cloudagent-python"
            )

        # run an ACA
        # command: aca-py start --admin 127.0.0.1 8020 --admin-insecure-mode --inbound-transport http 0.0.0.0 8000 --outbound-transport http
        cls.process = subprocess.Popen(  # nosec
            [
                "aca-py",
                "start",
                "--admin",
                cls.aca_admin_address,
                str(cls.aca_admin_port),
                "--admin-insecure-mode",
                "--inbound-transport",
                "http",
                "0.0.0.0",
                "8000",
                "--outbound-transport",
                "http",
            ]
        )
        time.sleep(4.0)

    @pytest.mark.asyncio
    async def test_connecting_to_aca(self):
        """Test connecting to aca."""
        configuration = ConnectionConfig(
            host=self.aca_admin_address,
            port=self.aca_admin_port,
            connection_id=HTTPClientConnection.connection_id,
        )
        http_client_connection = HTTPClientConnection(
            configuration=configuration,
            data_dir=MagicMock(),
            identity=self.aea_identity,
        )
        http_client_connection.loop = asyncio.get_event_loop()

        # Request messages
        request_http_message = HttpMessage(
            dialogue_reference=("1", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url="http://{}:{}/status".format(
                self.aca_admin_address, self.aca_admin_port
            ),
            headers="",
            version="",
            body=b"",
        )
        request_http_message.to = "ACA"
        request_envelope = Envelope(
            to="ACA",
            sender="AEA",
            message=request_http_message,
        )

        try:
            # connect to ACA
            await http_client_connection.connect()
            assert http_client_connection.is_connected is True

            # send request to ACA
            await http_client_connection.send(envelope=request_envelope)

            # receive response from ACA
            response_envelop = await http_client_connection.receive()

            # check the response
            assert response_envelop.to == self.aea_address
            assert response_envelop.sender == "HTTP Server"
            assert response_envelop.protocol_id == HttpMessage.protocol_id
            decoded_response_message = response_envelop.message
            assert (
                decoded_response_message.performative
                == HttpMessage.Performative.RESPONSE
            )
            assert decoded_response_message.version == ""
            assert decoded_response_message.status_code == 200
            assert decoded_response_message.status_text == "OK"
            assert decoded_response_message.headers is not None
            assert decoded_response_message.version is not None

        finally:
            # disconnect from ACA
            await http_client_connection.disconnect()
            assert http_client_connection.is_connected is False

    @pytest.mark.asyncio
    async def test_end_to_end_aea_aca(self):
        """Test the end to end aea aca interaction."""
        # AEA components
        wallet = Wallet({DEFAULT_LEDGER: DEFAULT_PRIVATE_KEY_FILE})
        identity = Identity(
            name="my_aea_1",
            address=wallet.addresses.get(DEFAULT_LEDGER),
            public_key=wallet.public_keys.get(DEFAULT_LEDGER),
            default_address_key=DEFAULT_LEDGER,
        )
        data_dir = MagicMock()
        configuration = ConnectionConfig(
            host=self.aca_admin_address,
            port=self.aca_admin_port,
            connection_id=HTTPClientConnection.connection_id,
        )
        http_client_connection = HTTPClientConnection(
            configuration=configuration,
            data_dir=MagicMock(),
            identity=identity,
        )
        resources = Resources()
        resources.add_connection(http_client_connection)

        # create AEA
        aea = AEA(identity, wallet, resources, data_dir)

        # Add http protocol to AEA resources
        http_protocol_configuration = ProtocolConfig.from_json(
            yaml.safe_load(
                open(
                    os.path.join(
                        self.cwd,
                        "packages",
                        "fetchai",
                        "protocols",
                        "http",
                        "protocol.yaml",
                    )
                )
            )
        )
        http_protocol = Protocol(http_protocol_configuration, HttpMessage.serializer())
        resources.add_protocol(http_protocol)

        # Request message & envelope
        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url="http://{}:{}/status".format(
                self.aca_admin_address, self.aca_admin_port
            ),
            headers="",
            version="",
            body=b"",
        )
        request_http_message.to = "ACA"
        request_envelope = Envelope(
            to="ACA",
            sender="AEA",
            message=request_http_message,
        )

        # add a simple skill with handler
        skill_context = SkillContext(aea.context)
        skill_config = SkillConfig(
            name="simple_skill", author="fetchai", version="0.1.0"
        )
        aea_handler = AEAHandler(skill_context=skill_context, name="aea_handler")
        simple_skill = Skill(
            skill_config, skill_context, handlers={aea_handler.name: aea_handler}
        )
        resources.add_skill(simple_skill)

        # add error skill to AEA
        error_skill = Skill.from_dir(
            os.path.join(AEA_DIR, "skills", "error"), agent_context=aea.context
        )
        resources.add_skill(error_skill)

        # start AEA thread
        t_aea = Thread(target=aea.start)
        try:
            t_aea.start()
            time.sleep(1.0)
            aea.outbox.put(request_envelope)
            time.sleep(5.0)
            assert (
                aea_handler.handled_message.performative
                == HttpMessage.Performative.RESPONSE
            )
            assert aea_handler.handled_message.version == ""
            assert aea_handler.handled_message.status_code == 200
            assert aea_handler.handled_message.status_text == "OK"
            assert aea_handler.handled_message.headers is not None
            assert aea_handler.handled_message.version is not None
        finally:
            aea.stop()
            t_aea.join()

    @classmethod
    def teardown_class(cls):
        """Teardown the aca."""
        # terminate the ACA
        cls.process.terminate()


class AEAHandler(Handler):
    """The handler for the AEA."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[PublicId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
