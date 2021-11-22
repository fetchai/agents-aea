#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""Check amount of time for acn connection start."""
import asyncio
import logging
import os
import time
from tempfile import TemporaryDirectory
from typing import Callable, List, Tuple, Union

from aea_cli_benchmark.case_acn_startup.utils import (
    _make_libp2p_client_connection,
    _make_libp2p_connection,
    _make_libp2p_mailbox_connection,
)

from aea.connections.base import Connection


async def _run_connect(con_maker: Callable[..., Connection]) -> float:
    logging.basicConfig(level=logging.CRITICAL)
    con = con_maker()
    start_time = time.time()
    await con.connect()
    assert con.is_connected
    connect_time = time.time() - start_time
    await con.disconnect()
    return connect_time


async def _run_libp2p_node() -> float:
    return await _run_connect(con_maker=lambda: _make_libp2p_connection("."))


async def _run_p2p_client() -> float:
    node_con = _make_libp2p_connection(".", delegate=True)
    await node_con.connect()
    try:
        return await _run_connect(
            con_maker=lambda: _make_libp2p_client_connection(
                peer_public_key=node_con.node.pub, data_dir="."
            ),
        )
    finally:
        await node_con.disconnect()


async def _run_p2p_mailbox() -> float:
    node_con = _make_libp2p_connection(".", mailbox=True)
    await node_con.connect()
    try:
        return await _run_connect(
            con_maker=lambda: _make_libp2p_mailbox_connection(
                peer_public_key=node_con.node.pub, data_dir="."
            ),
        )
    finally:
        await node_con.disconnect()


def run(connection: str) -> List[Tuple[str, Union[int, float]]]:
    """Check construction time and memory usage."""
    cwd = os.getcwd()
    try:
        with TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            if connection == "p2pnode":
                coro = _run_libp2p_node()
            elif connection == "client":
                coro = _run_p2p_client()
            elif connection == "mailbox":
                coro = _run_p2p_mailbox()
            else:
                raise ValueError(f"Unsupported connection: {connection}")

            connect_time = asyncio.get_event_loop().run_until_complete(coro)

            return [
                ("Connection time (seconds)", connect_time),
            ]
    finally:
        os.chdir(cwd)
