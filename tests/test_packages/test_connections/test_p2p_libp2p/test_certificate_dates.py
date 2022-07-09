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

import os
from datetime import datetime
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from packages.valory.connections import (
    p2p_libp2p,
    p2p_libp2p_client,
    p2p_libp2p_mailbox,
)
from packages.valory.connections.p2p_libp2p.consts import (
    LIBP2P_CERT_NOT_AFTER,
    LIBP2P_CERT_NOT_BEFORE,
)


P2P_LIBP2P_MODULES = (p2p_libp2p, p2p_libp2p_client, p2p_libp2p_mailbox)


@pytest.mark.parametrize("p2p_libp2p_module", P2P_LIBP2P_MODULES)
def test_certificate_dates(p2p_libp2p_module: ModuleType):
    """Test certificate dates not outdated"""

    def to_datetime(time: str) -> datetime:
        return datetime.strptime(time, date_format)

    path = Path(os.path.sep.join(p2p_libp2p_module.__name__.split(".")))
    data = yaml.safe_load((path.absolute() / "connection.yaml").read_text())

    date_format = "%Y-%m-%d"
    cert_requests = data["cert_requests"]

    for cert_request in cert_requests:
        not_before, not_after = cert_request["not_before"], cert_request["not_after"]
        assert not_before == LIBP2P_CERT_NOT_BEFORE
        assert not_after == LIBP2P_CERT_NOT_AFTER
        assert to_datetime(not_before) <= datetime.now() < to_datetime(not_after)
