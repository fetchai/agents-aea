# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""Settings for operating Registry with CLI."""


from typing import Dict, Tuple


REGISTRY_CONFIG_KEY: str = "registry_config"


REGISTRY_REMOTE = "remote"
REGISTRY_LOCAL = "local"

REGISTRY_TYPES: Tuple[str, ...] = (REGISTRY_LOCAL, REGISTRY_REMOTE)

REMOTE_HTTP = "http"
REMOTE_IPFS = "ipfs"

REGISTRY_API_URL_KEY = "registry_api_url"
# we ignore issue B105 because this is not an hard-coded authentication token,
# but the name of the field in the configuration file.
AUTH_TOKEN_KEY = "auth_token"  # nosec

DEFAULT_IPFS_URL = "/dns/registry.autonolas.tech/tcp/443/https"
DEFAULT_IPFS_URL_LOCAL = "/ip4/127.0.0.1/tcp/5001"

DEFAULT_REGISTRY_CONFIG: Dict = {
    "default": None,
    "settings": {
        REGISTRY_REMOTE: {
            "default": None,
            REMOTE_HTTP: {
                "auth_token": None,  # auth token for registry
                "registry_api_url": None,  # registry url
            },
            REMOTE_IPFS: {"ipfs_node": None},  # IPFS url (in multiaddr format)
        },
        REGISTRY_LOCAL: {"default_packages_path": None},
    },
}
