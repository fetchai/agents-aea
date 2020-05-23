# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Implementation of the 'aea interact' subcommand."""

import codecs
from typing import Optional

import click

from aea.configurations.base import PublicId
from aea.connections.stub.connection import (
    DEFAULT_INPUT_FILE_NAME,
    DEFAULT_OUTPUT_FILE_NAME,
    StubConnection,
)
from aea.mail.base import Envelope, InBox, Multiplexer, OutBox


class InterruptInputException(Exception):
    """An exception to mark an interuption event."""


def try_construct_envelope() -> Optional[Envelope]:
    """Try construct an envelope from user input."""
    envelope = None  # type: Optional[Envelope]
    try:
        print("Provide envelope to:")
        to = input()
        if to == "":
            raise InterruptInputException
        print("Provide envelope sender:")
        sender = input()
        if sender == "":
            raise InterruptInputException
        print("Provide envelope protocol_id:")
        protocol_id = input()
        if protocol_id == "":
            raise InterruptInputException
        print("Provide envelope message:")
        message_escaped = input()
        if message_escaped == "":
            raise InterruptInputException
        message = codecs.decode(message_escaped.encode("utf-8"), "unicode-escape")
        message_encoded = message.encode("utf-8")
        envelope = Envelope(
            to=to,
            sender=sender,
            protocol_id=PublicId.from_str(protocol_id),
            message=message_encoded,
        )
    except InterruptInputException:
        print("Interrupting input, checking inbox ...")
    except KeyboardInterrupt as e:
        raise e
    except Exception as e:
        print(e)
    return envelope


def run():
    stub_connection = StubConnection(
        input_file_path=DEFAULT_OUTPUT_FILE_NAME,
        output_file_path=DEFAULT_INPUT_FILE_NAME,
    )
    multiplexer = Multiplexer([stub_connection])
    inbox = InBox(multiplexer)
    outbox = OutBox(multiplexer)

    try:
        multiplexer.connect()
        is_running = True
        while is_running:
            try:
                envelope = try_construct_envelope()
                if envelope is None and not inbox.empty():
                    envelope = inbox.get_nowait()
                    assert (
                        envelope is not None
                    ), "Could not recover envelope from inbox."
                    print(
                        "Received envelope:\nto: {}\nsender: {}\nprotocol_id: {}\nmessage: {}\n".format(
                            envelope.to,
                            envelope.sender,
                            envelope.protocol_id,
                            envelope.message,
                        )
                    )
                elif envelope is None and inbox.empty():
                    print("Received no new envelope!")
                else:
                    outbox.put(envelope)
                    print(
                        "Sending envelope:\nto: {}\nsender: {}\nprotocol_id: {}\nmessage: {}\n".format(
                            envelope.to,
                            envelope.sender,
                            envelope.protocol_id,
                            envelope.message,
                        )
                    )
            except KeyboardInterrupt:
                is_running = False
            except Exception as e:
                print(e)
    finally:
        multiplexer.disconnect()


@click.command()
def interact():
    """Interact with a running AEA via the stub connection."""
    click.echo("Starting AEA interaction channel...")
    run()
