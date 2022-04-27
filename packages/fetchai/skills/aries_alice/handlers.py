# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
"""This package contains the handlers for the aries_alice skill."""
import json
from typing import Any, Dict, List, Optional, cast

from aea.common import Address
from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_alice.behaviours import AliceBehaviour
from packages.fetchai.skills.aries_alice.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_alice.strategy import (
    ADMIN_COMMAND_CREATE_INVITATION,
    ADMIN_COMMAND_RECEIVE_INVITE,
    Strategy,
)


class DefaultHandler(Handler):
    """This class represents alice's handler for default messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        message = cast(DefaultMessage, message)
        # recover dialogue
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_dialogue = cast(
            Optional[DefaultDialogue], default_dialogues.update(message)
        )
        if default_dialogue is None:
            self.context.logger.error(
                "alice -> default_handler -> handle(): something went wrong when adding the incoming default message to the dialogue."
            )
            return

        if message.performative == DefaultMessage.Performative.BYTES:
            content_bytes = message.content
            content = json.loads(content_bytes)
            self.context.logger.info("Received message content:" + repr(content))
            # accept invite
            if "@type" in content:
                strategy = cast(Strategy, self.context.strategy)
                strategy.invitations[content["@id"]] = message.sender
                self.context.behaviours.alice.send_http_request_message(
                    method="POST",
                    url=strategy.admin_url
                    + ADMIN_COMMAND_RECEIVE_INVITE
                    + "?auto_accept=true",
                    content=content,
                )

    def teardown(self) -> None:
        """Implement the handler teardown."""


class HttpHandler(Handler):
    """This class represents alice's handler for HTTP messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[PublicId]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.connected: Dict[str, Address] = {}  # conn_id: agent addr
        self.addr_names: Dict[Address, str] = {}  # agent addr: agent name
        self.connections_sent: Dict[str, Address] = {}  # conn_id: agent addr
        self.cred_def_id: Optional[str] = None
        self.presentation_requests: List[Dict] = []

    @property
    def invitations(self) -> Dict[str, str]:
        """Get list of invitation sent from the strategy object."""
        strategy = cast(Strategy, self.context.strategy)
        return strategy.invitations

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        message = cast(HttpMessage, message)
        strategy = cast(Strategy, self.context.strategy)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
        if http_dialogue is None:
            self.context.logger.error(
                "alice -> http_handler -> handle() -> REQUEST: something went wrong when adding the incoming HTTP webhook request message to the dialogue."
            )
            return

        if message.performative == HttpMessage.Performative.REQUEST:  # webhook
            content_bytes = message.body
            self.context.logger.info(
                "Received webhook message content:" + str(content_bytes)
            )
            content = json.loads(content_bytes)

            if "invitation_msg_id" in content:
                if content["invitation_msg_id"] in self.invitations:
                    if (
                        content["state"] == "active"
                        and content["connection_id"] not in self.connected
                    ):
                        self.context.logger.info(
                            f"Connected to {content['their_label']}"
                        )
                        self.connected[content["connection_id"]] = self.invitations[
                            content["invitation_msg_id"]
                        ]
                        name = content["their_label"]
                        self.addr_names[
                            self.invitations[content["invitation_msg_id"]]
                        ] = name
                        if name != "faber":
                            body = {
                                "connection_id": content["connection_id"],
                                "proof_request": {
                                    "name": "Proof of Education",
                                    "version": "1.0",
                                    "requested_attributes": {
                                        "0_name_uuid": {
                                            "name": "name",
                                            "restrictions": [
                                                {"cred_def_id": self.cred_def_id}
                                            ],
                                        },
                                        "0_date_uuid": {
                                            "name": "date",
                                            "restrictions": [
                                                {"cred_def_id": self.cred_def_id}
                                            ],
                                        },
                                        "0_degree_uuid": {
                                            "name": "degree",
                                            "restrictions": [
                                                {"cred_def_id": self.cred_def_id}
                                            ],
                                        },
                                        "0_self_attested_thing_uuid": {
                                            "name": "self_attested_thing"
                                        },
                                    },
                                    "requested_predicates": {},
                                },
                            }
                            self.context.behaviours.alice.send_http_request_message(
                                method="POST",
                                url=strategy.admin_url + "/present-proof/send-request",
                                content=body,
                            )
                            self.context.logger.info(
                                f"Sent credentials proof request to {name}"
                            )
            elif "presentation_request_dict" in content:
                if content["role"] == "prover":
                    if content["state"] == "request_received":
                        self.context.behaviours.alice.send_http_request_message(
                            method="GET",
                            url=strategy.admin_url
                            + f"/present-proof/records/{content['presentation_exchange_id']}/credentials",
                        )
                        self.presentation_requests.append(content)
                        self.context.logger.info("Got credentials proof request")
                elif (
                    content["role"] == "verifier"
                    and content["state"] == "presentation_received"
                ):
                    name = self.addr_names[self.connected[content["connection_id"]]]
                    self.context.logger.info(f"Got credentials proof from {name}")
            elif "credential_proposal_dict" in content:
                if content["state"] == "credential_acked":
                    self.cred_def_id = content["raw_credential"]["cred_def_id"]
                    self.context.logger.info(
                        f"Got crendetials from faber: schema:{self.cred_def_id} {content['credential_proposal_dict']['credential_proposal']}"
                    )

                    strategy.is_searching = True
                    self.context.behaviours.alice.perform_agents_search()
            else:
                self.context.logger.warning(f"unknown message {content}")
        elif (
            message.performative == HttpMessage.Performative.RESPONSE
        ):  # response to http_client request
            content_bytes = message.body
            content = json.loads(content_bytes)
            self.context.logger.info(f"Got response {content}")

            if "Error" in content:
                self.context.logger.error(
                    "Something went wrong after I sent the administrative command of 'invitation receive'"
                )
            elif "presentation_referents" in str(content):
                self._handle_creds_for_proof_request(content)
            else:
                self.context.logger.info(
                    f"Received http response message content:{str(content)}"
                )
                if "invitation" in content:
                    self._send_invitation_message(content)

    def _handle_creds_for_proof_request(self, credentials: Dict) -> None:
        self.context.logger.info("start proof generating")
        strategy = cast(Strategy, self.context.strategy)
        credentials_by_ref = {}  # type: ignore
        revealed = {}
        self_attested = {}
        predicates = {}
        if not self.presentation_requests:
            self.context.logger.warning("No presentastion requests pending")
            return
        presentation_request = self.presentation_requests.pop()
        if credentials:
            for row in credentials:
                for referent in row["presentation_referents"]:
                    if referent not in credentials_by_ref:
                        credentials_by_ref[referent] = row

        for referent in presentation_request["presentation_request"][
            "requested_attributes"
        ]:
            if referent in credentials_by_ref:
                revealed[referent] = {
                    "cred_id": credentials_by_ref[referent]["cred_info"]["referent"],
                    "revealed": True,
                }
            else:
                self_attested[referent] = "my self-attested value"

        for referent in presentation_request["presentation_request"][
            "requested_predicates"
        ]:
            if referent in credentials_by_ref:
                predicates[referent] = {
                    "cred_id": credentials_by_ref[referent]["cred_info"]["referent"],
                    "revealed": True,
                }

        request = {
            "requested_predicates": predicates,
            "requested_attributes": revealed,
            "self_attested_attributes": self_attested,
        }
        presentation_exchange_id = presentation_request["presentation_exchange_id"]
        self.context.behaviours.alice.send_http_request_message(
            method="POST",
            url=strategy.admin_url
            + "/present-proof/records/"
            + f"{presentation_exchange_id}/send-presentation",
            content=request,
        )
        self.context.logger.info("proof generated and sent")

    def _send_invitation_message(self, connection: Dict) -> None:
        """
        Send a default message to Alice.

        :param connection: the content of the connection message.
        """
        strategy = cast(Strategy, self.context.strategy)
        # context
        connections_unsent = list(
            set(strategy.aea_addresses) - set(self.connections_sent.values())
        )
        if not connections_unsent:
            self.context.logger.info(
                "Every invitation pushed, skip this new connection"
            )
            return
        target = connections_unsent[0]
        invitation = connection["invitation"]

        self.connections_sent[connection["connection_id"]] = target

        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        message, _ = default_dialogues.create(
            counterparty=target,
            performative=DefaultMessage.Performative.BYTES,
            content=json.dumps(invitation).encode("utf-8"),
        )
        # send
        self.context.outbox.put_message(message=message)

        self.context.logger.info(f"connection: {str(connection)}")
        self.context.logger.info(f"connection id: {connection['connection_id']}")  # type: ignore
        self.context.logger.info(f"invitation: {str(invitation)}")
        self.context.logger.info(
            f"Sent invitation to {target}. Waiting for the invitation from agent {target} to finalise the connection..."
        )

    def teardown(self) -> None:
        """Implement the handler teardown."""


class OefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
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
        if oef_search_msg.performative == OefSearchMessage.Performative.SUCCESS:
            self._handle_success(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the oef search message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_success(
        self,
        oef_search_success_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_success_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search success message={} in dialogue={}.".format(
                oef_search_success_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_success_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            description = target_message.service_description
            data_model_name = description.data_model.name
            registration_behaviour = cast(
                AliceBehaviour, self.context.behaviours.alice,
            )
            if "location_agent" in data_model_name:
                registration_behaviour.register_service()
            elif "set_service_key" in data_model_name:
                registration_behaviour.register_genus()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "genus"
            ):
                registration_behaviour.register_classification()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "classification"
            ):
                self.context.logger.info(
                    "the agent, with its genus and classification, and its service are successfully registered on the SOEF."
                )
            else:
                self.context.logger.warning(
                    f"received soef SUCCESS message as a reply to the following unexpected message: {target_message}"
                )

    def _handle_search(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle the search response.

        :param oef_search_msg: the oef search message to be handled
        """

        if len(oef_search_msg.agents) == 0:
            self.context.logger.info("No agents found. Keep searching")
            return

        self.context.logger.info(
            f"found agents {', '.join(oef_search_msg.agents)}, stopping search."
        )

        strategy = cast(Strategy, self.context.strategy)
        strategy.is_searching = False

        strategy.aea_addresses = list(oef_search_msg.agents)

        # send invitations
        for addr in strategy.aea_addresses:
            self.context.behaviours.alice.send_http_request_message(
                method="POST", url=strategy.admin_url + ADMIN_COMMAND_CREATE_INVITATION,
            )
            self.context.logger.info(f"created an invitation for {addr}.")

    def _handle_error(
        self,
        oef_search_error_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_error_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_error_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_error_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            alice_behaviour = cast(AliceBehaviour, self.context.behaviours.alice,)
            alice_behaviour.failed_registration_msg = target_message

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
