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

"""This test module contains negative tests for Libp2p tcp client connection."""

import pytest

from packages.valory.connections.p2p_libp2p_mailbox.connection import (
    P2PLibp2pMailboxConnection,
)

from tests.test_packages.test_connections.test_p2p_libp2p.base import (
    BaseP2PLibp2pTest,
    _make_libp2p_mailbox_connection,
)
from tests.test_packages.test_connections.test_p2p_libp2p_client.test_errors import (
    TestLibp2pClientConnectionFailureConnectionSetup as BaseFailureConnectionSetup,
)
from tests.test_packages.test_connections.test_p2p_libp2p_client.test_errors import (
    TestLibp2pClientConnectionFailureNodeNotConnected as BaseFailureNodeNotConnected,
)


@pytest.mark.asyncio
class TestLibp2pMailboxConnectionFailureNodeNotConnected(BaseFailureNodeNotConnected):
    """Test that connection fails when node not running"""

    public_key = BaseP2PLibp2pTest.default_crypto.public_key
    connection = _make_libp2p_mailbox_connection(peer_public_key=public_key)  # type: ignore
    # overwrite, no mailbox equivalent of P2PLibp2pClientConnection (TCPSocketChannelClient)
    test_connect_attempts = None


class TestLibp2pMailboxConnectionFailureConnectionSetup(BaseFailureConnectionSetup):
    """Test that connection fails when setup incorrectly"""

    connection_cls = P2PLibp2pMailboxConnection  # type: ignore
