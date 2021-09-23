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
import os
from typing import Optional, TYPE_CHECKING, Type, Union

import click

from aea.cli.utils.constants import STUB_CONNECTION
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.exceptions import InterruptInputException
from aea.common import Address
from aea.configurations.base import ConnectionConfig, PackageType, PublicId
from aea.configurations.constants import (
    CONNECTIONS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_PROTOCOL,
    PROTOCOLS,
    SIGNING_PROTOCOL,
    STATE_UPDATE_PROTOCOL,
    VENDOR,
)
from aea.configurations.loader import ConfigLoader
from aea.connections.base import Connection
from aea.crypto.wallet import CryptoStore
from aea.helpers.io import open_file
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.multiplexer import InBox, Multiplexer, OutBox
from aea.protocols.base import Protocol
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import Dialogues


if TYPE_CHECKING:  # pragma: nocover
    from packages.fetchai.connections.stub.connection import (  # noqa: F401
        DEFAULT_INPUT_FILE_NAME,
        DEFAULT_OUTPUT_FILE_NAME,
        StubConnection,
    )
    from packages.fetchai.protocols.default.dialogues import (  # noqa: F401
        DefaultDialogue,
        DefaultDialogues,
    )
    from packages.fetchai.protocols.default.message import DefaultMessage  # noqa: F401


@click.command()
@click.pass_context
@check_aea_project
def interact(
    click_context: click.core.Context,  # pylint: disable=unused-argument
) -> None:
    """Interact with the running agent via the stub connection."""
    click.echo("Starting AEA interaction channel...")
    _run_interaction_channel()


def _load_packages(agent_identity: Identity) -> None:
    """Load packages in the current interpreter."""
    default_protocol_id = PublicId.from_str(DEFAULT_PROTOCOL)
    Protocol.from_dir(
        os.path.join(
            VENDOR, default_protocol_id.author, PROTOCOLS, default_protocol_id.name
        )
    )
    signing_protocol_id = PublicId.from_str(SIGNING_PROTOCOL)
    Protocol.from_dir(
        os.path.join(
            VENDOR, signing_protocol_id.author, PROTOCOLS, signing_protocol_id.name
        )
    )
    state_update_protocol_id = PublicId.from_str(STATE_UPDATE_PROTOCOL)
    Protocol.from_dir(
        os.path.join(
            VENDOR,
            state_update_protocol_id.author,
            PROTOCOLS,
            state_update_protocol_id.name,
        )
    )
    stub_connection_id = PublicId.from_str(STUB_CONNECTION)
    Connection.from_dir(
        os.path.join(
            VENDOR, stub_connection_id.author, CONNECTIONS, stub_connection_id.name,
        ),
        agent_identity,
        CryptoStore(),
        os.getcwd(),
    )


def _run_interaction_channel() -> None:
    loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
    agent_configuration = loader.load(open_file(DEFAULT_AEA_CONFIG_FILE))
    agent_name = agent_configuration.name

    identity_stub = Identity(agent_name + "_interact", "interact", "interact")
    _load_packages(identity_stub)

    # load agent configuration file
    from packages.fetchai.connections.stub.connection import (  # noqa: F811 # pylint: disable=import-outside-toplevel
        DEFAULT_INPUT_FILE_NAME,
        DEFAULT_OUTPUT_FILE_NAME,
        StubConnection,
    )
    from packages.fetchai.protocols.default.dialogues import (  # noqa: F811 # pylint: disable=import-outside-toplevel
        DefaultDialogue,
        DefaultDialogues,
    )
    from packages.fetchai.protocols.default.message import (  # noqa: F811 # pylint: disable=import-outside-toplevel
        DefaultMessage,
    )

    # load stub connection
    configuration = ConnectionConfig(
        input_file=DEFAULT_OUTPUT_FILE_NAME,
        output_file=DEFAULT_INPUT_FILE_NAME,
        connection_id=StubConnection.connection_id,
    )

    stub_connection = StubConnection(
        configuration=configuration, data_dir=os.getcwd(), identity=identity_stub
    )
    multiplexer = Multiplexer([stub_connection])
    inbox = InBox(multiplexer)
    outbox = OutBox(multiplexer)

    def role_from_first_message(  # pylint: disable=unused-argument
        message: Message, receiver_address: Address
    ) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :param receiver_address: the address of the receiving agent
        :return: The role of the agent
        """
        return DefaultDialogue.Role.AGENT

    dialogues = DefaultDialogues(identity_stub.name, role_from_first_message)

    try:
        multiplexer.connect()
        while True:  # pragma: no cover
            _process_envelopes(agent_name, inbox, outbox, dialogues, DefaultMessage)

    except KeyboardInterrupt:
        click.echo("Interaction interrupted!")
    except BaseException as e:  # pylint: disable=broad-except # pragma: no cover
        click.echo(e)
    finally:
        multiplexer.disconnect()


def _process_envelopes(
    agent_name: str,
    inbox: InBox,
    outbox: OutBox,
    dialogues: Dialogues,
    message_class: Type[Message],
) -> None:
    """
    Process envelopes.

    :param agent_name: name of an agent.
    :param inbox: an inbox object.
    :param outbox: an outbox object.
    :param dialogues: the dialogues object.
    :param message_class: the message class.
    """
    envelope = _try_construct_envelope(agent_name, dialogues, message_class)
    if envelope is None:
        _check_for_incoming_envelope(inbox, message_class)
    else:
        outbox.put(envelope)
        click.echo(_construct_message("sending", envelope, message_class))


def _check_for_incoming_envelope(inbox: InBox, message_class: Type[Message]) -> None:
    if not inbox.empty():
        envelope = inbox.get_nowait()
        if envelope is None:
            raise ValueError("Could not recover envelope from inbox.")
        click.echo(_construct_message("received", envelope, message_class))
    else:
        click.echo("Received no new envelope!")


def _construct_message(
    action_name: str, envelope: Envelope, message_class: Type[Message]
) -> str:
    action_name = action_name.title()
    msg = (
        message_class.serializer.decode(envelope.message)
        if isinstance(envelope.message, bytes)
        else envelope.message
    )
    message = (
        "\n{} envelope:\nto: "
        "{}\nsender: {}\nprotocol_specification_id: {}\nmessage: {}\n".format(
            action_name,
            envelope.to,
            envelope.sender,
            envelope.protocol_specification_id,
            msg,
        )
    )
    return message


def _try_construct_envelope(
    agent_name: str, dialogues: Dialogues, message_class: Type[Message]
) -> Optional[Envelope]:
    """Try construct an envelope from user input."""
    envelope = None  # type: Optional[Envelope]
    try:
        performative_str = "bytes"
        performative = message_class.Performative(performative_str)
        click.echo(
            f"Provide message of protocol '{str(message_class.protocol_id)}' for performative {performative_str}:"
        )
        message_escaped = input()  # nosec
        message_escaped = message_escaped.strip()
        if message_escaped == "":
            raise InterruptInputException
        message_decoded = codecs.decode(
            message_escaped.encode("utf-8"), "unicode-escape"
        )
        message = message_decoded.encode("utf-8")  # type: Union[str, bytes]
        msg, _ = dialogues.create(
            counterparty=agent_name, performative=performative, content=message,
        )
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg,)
    except InterruptInputException:
        click.echo("Interrupting input, checking inbox ...")
    except KeyboardInterrupt:
        raise
    except BaseException as e:  # pylint: disable=broad-except # pragma: no cover
        click.echo(e)
    return envelope
