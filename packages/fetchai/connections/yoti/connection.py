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
"""Yoti connection implementation."""
import functools
import json
from typing import Any, Callable, Optional, cast

from yoti_python_sdk import Client as YotiClient  # type: ignore

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import BaseSyncConnection
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue

from packages.fetchai.protocols.yoti.dialogues import YotiDialogue
from packages.fetchai.protocols.yoti.dialogues import YotiDialogues as BaseYotiDialogues
from packages.fetchai.protocols.yoti.message import YotiMessage


PUBLIC_ID = PublicId.from_str("fetchai/yoti:0.6.0")


def rgetattr(obj: Any, attr: str, *args: Any) -> Any:
    """Recursive getattr."""

    def _getattr(obj: Any, attr: str) -> Any:
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


class YotiDialogues(BaseYotiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The yoti connection maintains the dialogue on behalf of the yoti server
            return YotiDialogue.Role.YOTI_SERVER

        BaseYotiDialogues.__init__(
            self,
            self_address=str(PUBLIC_ID),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class YotiConnection(BaseSyncConnection):
    """Proxy to the functionality of the SDK or API."""

    MAX_WORKER_THREADS = 5

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a connection to an SDK or API.

        :param kwargs: keyword arguments
        """
        super().__init__(**kwargs)
        yoti_client_sdk_id = cast(
            Optional[str], self.configuration.config.get("yoti_client_sdk_id")
        )
        yoti_key_file_path = cast(
            Optional[str], self.configuration.config.get("yoti_key_file_path")
        )
        if yoti_client_sdk_id is None or yoti_key_file_path is None:
            raise ValueError("Missing configuration.")
        self._client = YotiClient(yoti_client_sdk_id, yoti_key_file_path)
        self.dialogues = YotiDialogues()

    def on_connect(self) -> None:
        """Run on connect."""

    def on_disconnect(self) -> None:
        """Run on disconnect."""

    def on_send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        self.dispatch(envelope)

    def dispatch(self, envelope: Envelope) -> None:
        """
        Dispatch the request to the right sender handler.

        :param envelope: the envelope.
        :return: an awaitable.
        """
        if not isinstance(envelope.message, Message):  # pragma: nocover
            raise ValueError("Yoti connection expects non-serialized messages.")
        message = cast(YotiMessage, envelope.message)
        dialogue = cast(Optional[YotiDialogue], self.dialogues.update(message))
        if dialogue is None:
            raise ValueError(  # pragma: nocover
                "No dialogue created. Message={} not valid.".format(message)
            )
        performative = message.performative
        handler = self.get_handler(performative.value)
        response_message = handler(message, dialogue)

        if not response_message:
            self.logger.warning(f"Construct no response messge for {envelope}")
            return

        response_envelope = Envelope(
            to=envelope.sender,
            sender=envelope.to,
            message=response_message,
            context=envelope.context,
        )
        self.put_envelope(response_envelope)

    def get_handler(self, performative: str) -> Callable[[Message, Dialogue], Message]:
        """
        Get the handler method, given the message performative.

        :param performative: the message performative.
        :return: the method that will send the request.
        """
        handler = getattr(self, performative, None)
        if handler is None:
            raise Exception("Performative not recognized.")
        return handler

    def get_profile(self, message: YotiMessage, dialogue: YotiDialogue) -> YotiMessage:
        """
        Send the request 'get_request'.

        :param message: the Yoti message
        :param dialogue: the Yoti dialogue
        :return: the yoti message
        """
        activity_details = self._client.get_activity_details(message.token)
        if activity_details is None:
            response = self.get_error_message(
                ValueError("No activity_details returned"), message, dialogue
            )
            return response
        try:
            remember_me_id = activity_details.user_id
            profile = activity_details.profile
            if message.dotted_path == "":
                attributes = {
                    key: value.value
                    if isinstance(value.value, str)
                    else json.dumps(value.value)
                    for key, value in profile.attributes.items()
                }
                result = {"remember_me_id": remember_me_id, **attributes}
            else:
                callable_ = rgetattr(profile, message.dotted_path, *message.args)
                if len(message.args) != 0:
                    intermediate = callable_(*message.args)
                else:
                    intermediate = callable_
                result = {
                    "remember_me_id": remember_me_id,
                    "name": intermediate.name,
                    "value": intermediate.value,
                    "sources": ",".join(
                        [source.value for source in intermediate.sources]
                    ),
                    "verifiers": ",".join(
                        [verifier.value for verifier in intermediate.verifiers]
                    ),
                }
            response = cast(
                YotiMessage,
                dialogue.reply(
                    performative=YotiMessage.Performative.PROFILE,
                    target_message=message,
                    info=result,
                ),
            )
        except Exception as e:  # pylint: disable=broad-except
            response = self.get_error_message(e, message, dialogue)
            if self._logger:
                self._logger.exception("Error during envelope handling")
        return response

    @staticmethod
    def get_error_message(
        e: Exception, message: YotiMessage, dialogue: YotiDialogue,
    ) -> YotiMessage:
        """
        Build an error message.

        :param e: the exception
        :param message: the received message.
        :param dialogue: the dialogue.
        :return: an error message response.
        """
        response = cast(
            YotiMessage,
            dialogue.reply(
                performative=YotiMessage.Performative.ERROR,
                target_message=message,
                error_code=500,
                error_msg=str(e),
            ),
        )
        return response
