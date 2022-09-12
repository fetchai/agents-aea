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
"""Memory usage of dialogues across the time."""
import time
import uuid
from typing import List, Tuple, Union, cast

from aea_cli_benchmark.utils import get_mem_usage_in_mb  # noqa: I100

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue

from packages.fetchai.protocols.http.dialogues import HttpDialogue, HttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage


class DialogueHandler:
    """Generate messages and process with dialogues."""

    def __init__(self) -> None:
        """Set dialogues."""
        # pylint: disable=unused-argument

        def role(m: Message, addr: Address) -> Dialogue.Role:
            return HttpDialogue.Role.CLIENT

        self.addr = self.random_string
        self.dialogues = HttpDialogues(self.addr, role_from_first_message=role)

    @property
    def random_string(self) -> str:
        """Get random string on every access."""
        return uuid.uuid4().hex

    def process_message(self) -> None:
        """Process a message with dialogues."""
        message = self.create()
        dialogue = self.update(message)
        self.reply(dialogue, message)

    def update(self, message: HttpMessage) -> HttpDialogue:
        """Update dialogues with message."""
        return cast(HttpDialogue, self.dialogues.update(message))

    @staticmethod
    def reply(dialogue: HttpDialogue, message: HttpMessage) -> Message:
        """Construct and send a response for message received."""
        return dialogue.reply(
            target_message=message,
            performative=HttpMessage.Performative.RESPONSE,
            version=message.version,
            headers="",
            status_code=200,
            status_text="Success",
            body=message.body,
        )

    def create(self) -> HttpMessage:
        """Make initial http request."""
        message = HttpMessage(
            dialogue_reference=HttpDialogues.new_self_initiated_dialogue_reference(),
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="some url",
            headers="",
            version="",
            body=b"",
        )
        message.sender = self.random_string
        message.to = self.addr
        return message


def run(messages_amount: int) -> List[Tuple[str, Union[float, int]]]:
    """Test messages generation and memory consumption with dialogues."""
    handler = DialogueHandler()
    mem_usage_on_start = get_mem_usage_in_mb()
    start_time = time.time()
    for _ in range(messages_amount):
        handler.process_message()
    mem_usage = get_mem_usage_in_mb()

    return [
        ("Mem usage(Mb)", mem_usage - mem_usage_on_start),
        ("Time (seconds)", time.time() - start_time),
    ]
