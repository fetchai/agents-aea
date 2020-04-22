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

"""This package contains a scaffold of a handler."""

import json
from typing import Dict, Optional

from aea.configurations.base import ProtocolId
from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

HTTP_PROTOCOL_PUBLIC_ID = PublicId("fetchai", "http", "0.1.0")
ADMIN_HOST = "127.0.0.1"
ADMIN_PORT = 8020
SUPPORT_REVOCATION = False

class AriesDemoHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, admin_host: str = None, admin_port: int = None, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.admin_host = admin_host if not None else ADMIN_HOST
        self.admin_post = admin_port if not None else ADMIN_PORT

        self.admin_url = "http://{}:{}".format(self.admin_host, self.admin_post)

        self.kwargs = kwargs
        self.handled_message = None

    def _admin_post(self, path: str, content: Dict = None):
        # Request message & envelope
        request_http_message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
            method="POST",
            url=self.admin_url + path,
            headers="",
            version="",
            bodyy=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        self.context.outbox.put_message(
            to="Faber_ACA",
            sender=self.context.agent_address,
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
        )

    def _admin_get(self, path: str, content: Dict = None):
        # Request message & envelope
        request_http_message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url=self.admin_url + path,
            headers="",
            version="",
            bodyy=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        self.context.outbox.put_message(
            to="Faber_ACA",
            sender=self.context.agent_address,
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
        )

    # def register_did(self, ledger_url: str = None, alias: str = None):
    # self.log(f"Registering {self.ident} with seed {self.seed}")
    # if not ledger_url:
    #     ledger_url = LEDGER_URL
    # if not ledger_url:
    #     ledger_url = f"http://{self.external_host}:9000"
    # data = {"alias": alias or self.ident, "seed": self.seed, "role": "TRUST_ANCHOR"}
    # async with self.client_session.post(
    #     ledger_url + "/register", json=data
    # ) as resp:
    #     if resp.status != 200:
    #         raise Exception(f"Error registering DID, response code {resp.status}")
    #     nym_info = await resp.json()
    #     self.did = nym_info["did"]
    # self.log(f"Got DID: {self.did}")

    def register_schema(self, schema_name, version, schema_attrs):
        # Create a schema
        schema_body = {
            "schema_name": schema_name,
            "schema_version": version,
            "attributes": schema_attrs,
        }
        self._admin_post("/schemas", schema_body)

    def register_creddef(self, schema_id):
        # Create a cred def for the schema
        credential_definition_body = {
            "schema_id": schema_id,
            "support_revocation": SUPPORT_REVOCATION
        }
        self._admin_post(
            "/credential-definitions", credential_definition_body
        )

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass  # pragma: no cover

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        :return: None
        """
        # self.context.behaviours.aries_demo_behaviour.put(message)

        self.handled_message = message
        # import pdb;pdb.set_trace()
        if message.performative == HttpMessage.Performative.RESPONSE and message.status_code == 200:
            content_bytes = message.bodyy
            content = json.loads(content_bytes)
            self.context.logger.info("Received message: " + str(content))
            if "version" in content:  # response to /status
                # self.register_did()
                # self.register_schema(
                #     schema_name="degree schema",
                #     version="0.0.1",
                #     schema_attrs=["name", "date", "degree", "age", "timestamp"],
                # )
            # elif "schema_id" in content:
            #     schema_id = content["schema_id"]
            #     self.register_creddef(schema_id)
            # elif "credential_definition_id" in content:
            #     credential_definition_id = content["credential_definition_id"]
                self._admin_post("/connections/create-invitation")
            elif "connection_id" in content:
                connection_id = content["connection_id"]
                self.context.logger.info("Sent invitation to Alice. Waiting for the invitation from Alice to finalise the connection...")

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
