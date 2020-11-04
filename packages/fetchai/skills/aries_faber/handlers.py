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

"""This package contains the handlers for the faber_alice skill."""

import json
import random
from typing import Dict, Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.dialogues import (
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_faber.strategy import (
    ADMIN_COMMAND_CREATE_INVITATION,
    ADMIN_COMMAND_CREDDEF,
    ADMIN_COMMAND_SCEHMAS,
    ADMIN_COMMAND_STATUS,
    FABER_ACA_IDENTITY,
    FaberStrategy,
    LEDGER_COMMAND_REGISTER_DID,
)


SUPPORT_REVOCATION = False


class FaberHTTPHandler(Handler):
    """This class represents faber's handler for default messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[PublicId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        # ACA stuff
        self.faber_identity = FABER_ACA_IDENTITY
        rand_name = str(random.randint(100_000, 999_999))  # nosec
        # use my_name to manually use the same seed in this demo and when starting up the accompanying ACA
        # use rand_name to not use any seed when starting up the accompanying ACA
        self.seed = ("my_seed_000000000000000000000000" + rand_name)[-32:]
        self.did = None  # type: Optional[str]
        self.schema_id = None  # type: Optional[str]
        self.credential_definition_id = None  # type: Optional[str]

        # Helpers
        self.connection_id = None  # type: Optional[str]
        self.is_connected_to_Alice = False

        # AEA stuff
        self.handled_message = None

    def _send_default_message(self, content: Dict) -> None:
        """
        Send a default message to Alice.

        :param content: the content of the message.
        :return: None
        """
        # context
        strategy = cast(FaberStrategy, self.context.strategy)
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)

        # default message
        message, _ = default_dialogues.create(
            counterparty=strategy.alice_aea_address,
            performative=DefaultMessage.Performative.BYTES,
            content=json.dumps(content).encode("utf-8"),
        )
        # send
        self.context.outbox.put_message(message=message)

    def _register_did(self) -> None:
        """
        Register DID on the ledger.

        :return: None
        """
        strategy = cast(FaberStrategy, self.context.strategy)
        self.context.logger.info("Registering Faber_ACA with seed " + str(self.seed))
        data = {"alias": self.faber_identity, "seed": self.seed, "role": "TRUST_ANCHOR"}
        self.context.behaviours.faber.send_http_request_message(
            method="POST",
            url=strategy.ledger_url + LEDGER_COMMAND_REGISTER_DID,
            content=data,
        )

    def _register_schema(self, schema_name, version, schema_attrs) -> None:
        """
        Register schema definition.

        :param schema_name: the name of the schema
        :param version: the version of the schema
        :param schema_attrs: the attributes of the schema

        :return: None
        """
        strategy = cast(FaberStrategy, self.context.strategy)
        schema_body = {
            "schema_name": schema_name,
            "schema_version": version,
            "attributes": schema_attrs,
        }
        self.context.logger.info("Registering schema " + str(schema_body))
        # The following call isn't responded to. This is most probably because of missing options when running the accompanying ACA.
        # THe accompanying ACA is not properly connected to the von network ledger (missing pointer to genesis file/wallet type)
        self.context.behaviours.faber.send_http_request_message(
            method="POST",
            url=strategy.admin_url + ADMIN_COMMAND_SCEHMAS,
            content=schema_body,
        )

    def _register_creddef(self, schema_id) -> None:
        """
        Register credential definition.

        :param schema_id: the id of the schema definition registered on the ledger
        :return: None
        """
        strategy = cast(FaberStrategy, self.context.strategy)
        credential_definition_body = {
            "schema_id": schema_id,
            "support_revocation": SUPPORT_REVOCATION,
        }
        self.context.behaviours.faber.send_http_request_message(
            method="POST",
            url=strategy.admin_url + ADMIN_COMMAND_CREDDEF,
            content=credential_definition_body,
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
        message = cast(HttpMessage, message)
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        strategy = cast(FaberStrategy, self.context.strategy)

        self.handled_message = message
        if (
            message.performative == HttpMessage.Performative.RESPONSE
            and message.status_code == 200
        ):  # response to http request
            http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
            if http_dialogue is None:
                self.context.logger.exception(
                    "faber -> http_handler -> handle() -> RESPONSE: "
                    "something went wrong when adding the incoming HTTP response message to the dialogue."
                )
                return

            content_bytes = message.body  # type: ignore
            content = json.loads(content_bytes)
            self.context.logger.info("Received message: " + str(content))
            if "version" in content:  # response to /status
                self._register_did()
            elif "did" in content:
                self.did = content["did"]
                if self.did is not None:
                    self.context.logger.info("Got DID: " + self.did)
                else:
                    self.context.logger.info("DID is None")
                self._register_schema(
                    schema_name="degree schema",
                    version="0.0.1",
                    schema_attrs=["name", "date", "degree", "age", "timestamp"],
                )
            elif "schema_id" in content:
                self.schema_id = content["schema_id"]
                self._register_creddef(self.schema_id)
            elif "credential_definition_id" in content:
                self.credential_definition_id = content["credential_definition_id"]
                self.context.behaviours.faber.send_http_request_message(
                    method="POST",
                    url=strategy.admin_url + ADMIN_COMMAND_CREATE_INVITATION,
                )
            elif "connection_id" in content:
                connection = content
                self.connection_id = content["connection_id"]
                invitation = connection["invitation"]
                self.context.logger.info("connection: " + str(connection))
                self.context.logger.info("connection id: " + self.connection_id)  # type: ignore
                self.context.logger.info("invitation: " + str(invitation))
                self.context.logger.info(
                    "Sent invitation to Alice. Waiting for the invitation from Alice to finalise the connection..."
                )
                self._send_default_message(invitation)
        elif (
            message.performative == HttpMessage.Performative.REQUEST
        ):  # webhook request
            http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
            if http_dialogue is None:
                self.context.logger.exception(
                    "faber -> http_handler -> handle() -> REQUEST: "
                    "something went wrong when adding the incoming HTTP webhook request message to the dialogue."
                )
                return
            content_bytes = message.body
            content = json.loads(content_bytes)
            self.context.logger.info("Received webhook message content:" + str(content))
            if "connection_id" in content:
                if content["connection_id"] == self.connection_id:
                    if content["state"] == "active" and not self.is_connected_to_Alice:
                        self.context.logger.info("Connected to Alice")
                        self.is_connected_to_Alice = True

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class FaberOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.context.logger.info("Handling SOEF message...")
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the oef search message to be handled
        :return: None
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message to be handled
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle the search response.

        :param oef_search_msg: the oef search message to be handled
        :return: None
        """
        if len(oef_search_msg.agents) != 1:
            self.context.logger.info(
                "did not find Alice. found {} agents. continue searching.".format(
                    len(oef_search_msg.agents)
                )
            )
            return

        self.context.logger.info(
            "found Alice with address {}, stopping search.".format(
                oef_search_msg.agents[0]
            )
        )
        strategy = cast(FaberStrategy, self.context.strategy)
        strategy.is_searching = False  # stopping search

        # set alice address
        strategy.alice_aea_address = oef_search_msg.agents[0]

        # check ACA is running
        self.context.behaviours.faber.send_http_request_message(
            "GET", strategy.admin_url + ADMIN_COMMAND_STATUS
        )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
