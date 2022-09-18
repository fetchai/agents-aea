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
"""Check amount of time for acn connection communications."""
import asyncio
import logging
import os
import time
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Callable, List, Tuple, Union

from aea_cli_benchmark.case_acn_communication.utils import (
    DEFAULT_DELEGATE_PORT,
    DEFAULT_MAILBOX_PORT,
    DEFAULT_NODE_PORT,
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    _make_libp2p_mailbox_connection,
)

from aea.connections.base import Connection
from aea.mail.base import Envelope

from packages.fetchai.protocols.default.message import DefaultMessage


class TimeMeasure:
    """Time measure data class."""

    def __init__(self):
        """Init data class instance."""
        self.time = -1


@contextmanager
def time_measure():
    """Get time measure context."""
    start = time.time()
    m = TimeMeasure()
    try:
        yield m
    finally:
        m.time = time.time() - start


def make_envelope(from_addr: str, to_addr: str) -> Envelope:
    """Construct an envelope."""
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    envelope = Envelope(
        to=to_addr,
        sender=from_addr,
        message=msg,
    )
    return envelope


async def _run(con_maker: Callable[..., Connection]) -> Tuple[float, float]:
    """Run test case and return times for the first and the second messages sent over ACN."""
    try:
        connections = []
        genesis_node = _make_libp2p_connection(".", relay=True)
        await genesis_node.connect()
        connections.append(genesis_node)
        genesis_multiaddr = genesis_node.node.multiaddrs[0]

        relay_node1 = _make_libp2p_connection(
            ".",
            relay=True,
            entry_peers=[genesis_multiaddr],
            port=DEFAULT_NODE_PORT + 1,
            mailbox=True,
            delegate=True,
            mailbox_port=DEFAULT_MAILBOX_PORT + 1,
            delegate_port=DEFAULT_DELEGATE_PORT + 1,
        )
        await relay_node1.connect()
        connections.append(relay_node1)
        relay_node2 = _make_libp2p_connection(
            ".",
            relay=True,
            entry_peers=[genesis_multiaddr],
            port=DEFAULT_NODE_PORT + 2,
            mailbox=True,
            delegate=True,
            mailbox_port=DEFAULT_MAILBOX_PORT + 2,
            delegate_port=DEFAULT_DELEGATE_PORT + 2,
        )
        await relay_node2.connect()
        connections.append(relay_node2)

        relay_node1_multiaddr = relay_node1.node.multiaddrs[0]
        relay_node2_multiaddr = relay_node2.node.multiaddrs[0]
        await asyncio.sleep(1)
        con1 = con_maker(
            port=DEFAULT_NODE_PORT + 10,
            entry_peer=relay_node1_multiaddr,
            mailbox_port=DEFAULT_MAILBOX_PORT + 1,
            delegate_port=DEFAULT_DELEGATE_PORT + 1,
            pub_key=relay_node1.node.pub,
        )
        await con1.connect()
        connections.append(con1)

        con2 = con_maker(
            port=DEFAULT_NODE_PORT + 20,
            entry_peer=relay_node2_multiaddr,
            mailbox_port=DEFAULT_MAILBOX_PORT + 2,
            delegate_port=DEFAULT_DELEGATE_PORT + 2,
            pub_key=relay_node2.node.pub,
        )
        await con2.connect()
        connections.append(con2)

        envelope = make_envelope(con1.address, con2.address)

        with time_measure() as tm:
            await con1.send(envelope)
            envelope = await con2.receive()
        first_time = tm.time

        with time_measure() as tm:
            await con1.send(envelope)
            envelope = await con2.receive()

        second_time = tm.time

        return first_time, second_time

    finally:
        for con in reversed(connections):
            await con.disconnect()


def run(connection: str, run_times: int = 10) -> List[Tuple[str, Union[int, float]]]:
    """Check construction time and memory usage."""
    logging.basicConfig(level=logging.CRITICAL)
    cwd = os.getcwd()
    try:
        if connection == "p2pnode":

            def con_maker(
                port: int,
                entry_peer: str,
                mailbox_port: int,
                delegate_port: int,
                pub_key: str,
            ):
                return _make_libp2p_connection(".", port=port, entry_peers=[entry_peer])

        elif connection == "client":

            def con_maker(
                port: int,
                entry_peer: str,
                mailbox_port: int,
                delegate_port: int,
                pub_key: str,
            ):
                return _make_libp2p_client_connection(
                    peer_public_key=pub_key, data_dir=".", node_port=delegate_port
                )

        elif connection == "mailbox":

            def con_maker(
                port: int,
                entry_peer: str,
                mailbox_port: int,
                delegate_port: int,
                pub_key: str,
            ):
                return _make_libp2p_mailbox_connection(
                    peer_public_key=pub_key, data_dir=".", node_port=mailbox_port
                )

        else:
            raise ValueError(f"Unsupported connection: {connection}")

        with TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            coro = _run(con_maker)
            first_time, second_time = asyncio.get_event_loop().run_until_complete(coro)

            return [
                ("first time (seconds)", first_time),
                ("second time (seconds)", second_time),
            ]
    finally:
        os.chdir(cwd)
