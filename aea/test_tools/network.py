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

"""Helper utils."""

import socket
from urllib.parse import urlparse


LOCALHOST = urlparse("http://127.0.0.1")


def get_unused_tcp_port() -> int:
    """Get an unused TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((LOCALHOST.hostname, 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def get_host() -> str:
    """Get the host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:  # pylint: disable=broad-except
        IP = LOCALHOST.hostname
    finally:
        s.close()
    return IP
