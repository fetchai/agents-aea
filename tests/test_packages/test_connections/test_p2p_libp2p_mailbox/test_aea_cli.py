# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This test module contains AEA cli tests for Libp2p tcp client connection."""

from packages.valory.connections import p2p_libp2p_mailbox
from packages.valory.connections.p2p_libp2p_mailbox.connection import PUBLIC_ID

from tests.conftest import DEFAULT_HOST
from tests.test_packages.test_connections.test_p2p_libp2p.base import ports
from tests.test_packages.test_connections.test_p2p_libp2p_client.test_aea_cli import (
    TestP2PLibp2pClientConnectionAEARunning as Base,
)


class TestP2PLibp2pMailboxConnectionAEARunning(Base):
    """Test AEA with p2p_libp2p_client connection is correctly run"""

    conn_path = (
        p2p_libp2p_mailbox_path
    ) = f"vendor.{p2p_libp2p_mailbox.__name__.split('.', 1)[-1]}"
    public_id = str(PUBLIC_ID)
    port = next(ports)
    uri = f"{DEFAULT_HOST}:{port}"
    kwargs = dict(
        delegate_host=DEFAULT_HOST,
        mailbox_port=port,
        delegate=True,
        mailbox=True,
    )
