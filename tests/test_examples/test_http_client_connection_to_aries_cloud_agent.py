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

"""End-to-end test for AEA connecting using HTTP Client connection, to an Aries Cloud Agent."""

import asyncio
import logging
import os
import shutil
import sys
import time
from threading import Thread

import yaml

import pytest

from aea import AEA_DIR
from aea.aea import AEA
from aea.configurations.base import (
    ProtocolConfig,
    PublicId,
)
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message, Protocol

from aea.registries.base import Resources
from aea.skills.base import Handler, Skill, SkillContext

from packages.fetchai.connections.http_client.connection import HTTPClientConnection
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

from ..conftest import HTTP_PROTOCOL_PUBLIC_ID


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

        cls.cwd = os.getcwd()

        # check Aries Cloud Agents is installed
        res = shutil.which("aca-py")
        if res is None:
            print(
                "Please install Aries Cloud Agents first! See the following link: https://github.com/hyperledger/aries-cloudagent-python"
            )
            sys.exit(1)

    @pytest.mark.asyncio
    async def test_connecting_to_aca(self):
        http_client_connection = HTTPClientConnection(
            agent_address=self.aea_address,
            provider_address=self.aca_admin_address,
            provider_port=self.aca_admin_port,
        )
        http_client_connection.loop = asyncio.get_event_loop()

        # Request messages
        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url="http://{}:{}/status".format(self.aca_admin_address, self.aca_admin_port),
            headers="",
            version="",
            bodyy=b"",
        )
        request_envelope = Envelope(
            to="ACA",
            sender="AEA",
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
        )

        try:
            await http_client_connection.connect()
            assert http_client_connection.connection_status.is_connected is True

            await http_client_connection.send(envelope=request_envelope)

            response_envelop = await http_client_connection.receive()

            assert response_envelop.to == self.aea_address
            assert response_envelop.sender == "HTTP Server"
            assert response_envelop.protocol_id == HTTP_PROTOCOL_PUBLIC_ID
            decoded_response_message = HttpSerializer().decode(response_envelop.message)
            assert decoded_response_message.performative == HttpMessage.Performative.RESPONSE
            assert decoded_response_message.version == ""
            assert decoded_response_message.status_code == 200
            assert decoded_response_message.status_text == "OK"
            assert decoded_response_message.headers is not None
            assert decoded_response_message.version is not None

        finally:
            await http_client_connection.disconnect()
            assert http_client_connection.connection_status.is_connected is False

    @pytest.mark.asyncio
    async def test_connection(self):
        # AEA components
        ledger_apis = LedgerApis({}, FETCHAI)
        wallet = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})
        identity = Identity(
            name="my_aea_1",
            address=wallet.addresses.get(FETCHAI),
            default_address_key=FETCHAI,
        )
        http_client_connection = HTTPClientConnection(
            agent_address=self.aea_address,
            provider_address=self.aca_admin_address,
            provider_port=self.aca_admin_port,
        )

        resources = Resources()

        # create AEA
        aea = AEA(identity, [http_client_connection], wallet, ledger_apis, resources)

        # Add http protocol to resources
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
        http_protocol = Protocol(
            HttpMessage.protocol_id,
            HttpSerializer(),
            http_protocol_configuration,
        )
        resources.protocol_registry.register(
            HttpMessage.protocol_id, http_protocol
        )

        # Request messages
        request_http_message = HttpMessage(
            dialogue_reference=("", ""),
            target=0,
            message_id=1,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url="http://{}:{}/status".format(self.aca_admin_address, self.aca_admin_port),
            headers="",
            version="",
            bodyy=b"",
        )
        request_envelope = Envelope(
            to="ACA",
            sender="AEA",
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
        )

        # add handlers to AEA resources
        aea_handler = AEAHandler(
            skill_context=SkillContext(aea.context), name="fake_skill"
        )
        resources.handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                HttpMessage.protocol_id,
            ),
            aea_handler,
        )

        # add error skill to AEA
        error_skill = Skill.from_dir(
            os.path.join(AEA_DIR, "skills", "error"), aea.context
        )
        resources.add_skill(error_skill)

        # Start threads
        t_aea = Thread(target=aea.start)
        try:
            t_aea.start()
            time.sleep(1.0)
            aea.outbox.put(request_envelope)
            time.sleep(5.0)
            assert aea_handler.handled_message.performative == HttpMessage.Performative.RESPONSE
            assert aea_handler.handled_message.version == ""
            assert aea_handler.handled_message.status_code == 200
            assert aea_handler.handled_message.status_text == "OK"
            assert aea_handler.handled_message.headers is not None
            assert aea_handler.handled_message.version is not None
        finally:
            aea.stop()
            t_aea.join()


class AEAHandler(Handler):
    """The handler for the aea."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[ProtocolId]

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