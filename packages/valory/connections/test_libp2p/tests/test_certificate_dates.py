# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This test module ensures the dates on certificates are not outdated on issuance"""

# pylint: skip-file

from datetime import datetime
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from packages.valory.connections.p2p_libp2p.consts import (
    LIBP2P_CERT_NOT_AFTER,
    LIBP2P_CERT_NOT_BEFORE,
)


CONNECTIONS = Path(__file__).parent.parent.parent

P2P_LIBP2P_MODULES = (
    CONNECTIONS / "p2p_libp2p",
    CONNECTIONS / "p2p_libp2p_client",
    CONNECTIONS / "p2p_libp2p_mailbox",
)


@pytest.mark.parametrize("path", P2P_LIBP2P_MODULES)
def test_certificate_dates(path: ModuleType) -> None:
    """Test certificate dates not outdated"""

    def to_datetime(time: str) -> datetime:
        return datetime.strptime(time, date_format)

    data = yaml.safe_load((path / "connection.yaml").read_text())

    date_format = "%Y-%m-%d"
    cert_requests = data["cert_requests"]

    for cert_request in cert_requests:
        not_before, not_after = cert_request["not_before"], cert_request["not_after"]
        assert not_before == LIBP2P_CERT_NOT_BEFORE
        assert not_after == LIBP2P_CERT_NOT_AFTER
        assert to_datetime(not_before) <= datetime.now() < to_datetime(not_after)
