# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Module wrapping the helpers of public and private key cryptography."""

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import logging
from pathlib import Path

from fetchai.ledger.crypto import Entity  # type: ignore
from eth_account import Account  # type: ignore

from aea.crypto.base import DefaultCrypto
from aea.crypto.wallet import SUPPORTED_CRYPTOS
from aea.configurations.loader import ConfigLoader
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE
from aea.cli.common import Context

DEFAULT_PRIVATE_KEY_FILE = 'default_private_key.pem'
FETCHAI_PRIVATE_KEY_FILE = 'fet_private_key.txt'
ETHEREUM_PRIVATE_KEY_FILE = 'eth_private_key.txt'

logger = logging.getLogger(__name__)


def _verify_or_create_private_keys(ctx: Context) -> None:
    """
    Verify or create private keys.

    :param ctx: Context
    """
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
    fp = open(str(path), mode="r", encoding="utf-8")
    aea_conf = agent_loader.load(fp)

    for identifier in aea_conf.private_key_paths.keys():
        if identifier not in SUPPORTED_CRYPTOS:
            ValueError("Unsupported identifier in private key paths.")

    if aea_conf.private_key_paths['default'] == "" or aea_conf.private_key_paths['default'] is None:
        default_private_key_path = _create_temporary_private_key_pem_path()
        aea_conf.private_key_paths['default'] = default_private_key_path
    else:
        _try_validate_private_key_pem_path(aea_conf.private_key_paths['default'])

    if aea_conf.private_key_paths['fetchai'] == "" or aea_conf.private_key_paths['fetchai'] is None:
        path = Path(FETCHAI_PRIVATE_KEY_FILE)
        entity = Entity()
        with open(path, "w+") as file:
            file.write(entity.private_key_hex)
        fetchai_private_key_path = FETCHAI_PRIVATE_KEY_FILE
        aea_conf.private_key_paths['fetchai'] = fetchai_private_key_path
    else:
        _try_validate_fet_private_key_path(aea_conf.private_key_paths['fetchai'])

    if aea_conf.private_key_paths['ethereum'] == "" or aea_conf.private_key_paths['ethereum'] is None:
        path = Path(FETCHAI_PRIVATE_KEY_FILE)
        account = Account.create()
        with open(path, "w+") as file:
            file.write(account.privateKey.hex())
        ethereum_private_key_path = ETHEREUM_PRIVATE_KEY_FILE
        aea_conf.private_key_paths['ethereum'] = ethereum_private_key_path
    else:
        _try_validate_fet_private_key_path(aea_conf.private_key_paths['ethereum'])

    # update aea config
    path = Path(DEFAULT_AEA_CONFIG_FILE)
    fp = open(str(path), mode="w", encoding="utf-8")
    agent_loader.dump(aea_conf, fp)


def _create_temporary_private_key() -> bytes:
    """
    Create a temporary private key.

    :return: the private key in pem format.
    """
    crypto = DefaultCrypto()
    pem = crypto._private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())  # type: ignore
    return pem


def _try_validate_private_key_pem_path(private_key_pem_path: str) -> None:
    """
    Try to validate a private key.

    :param private_key_pem_path: the path to the private key.
    :return: None
    :raises: an exception if the private key is invalid.
    """
    try:
        DefaultCrypto(private_key_pem_path=private_key_pem_path)
    except ValueError:
        logger.error("This is not a valid private key file: '{}'".format(private_key_pem_path))
        exit(-1)


def _try_validate_fet_private_key_path(private_key_path:str) -> None:
    """
       Try to validate a private key.

       :param private_key_path: the path to the private key.
       :return: None
       :raises: an exception if the private key is invalid.
       """
    try:
        # TODO :Change this to match the enity.fromhex()
        with open(private_key_path, "r") as key:
            data = key.read()
            entity = Entity.from_hex(data)
    except ValueError:
        logger.error("This is not a valid private key file: '{}'".format(private_key_path))
        exit(-1)


def _try_validate_ethereum_private_key_path(private_key_path:str) -> None:
    """
           Try to validate a private key.

           :param private_key_path: the path to the private key.
           :return: None
           :raises: an exception if the private key is invalid.
           """
    try:
        # TODO :Change this to match the Account.fromhex()
        with open(private_key_path, "r") as key:
            data = key.read()
            account = Account.from_key(data)
    except ValueError:
        logger.error("This is not a valid private key file: '{}'".format(private_key_path))
        exit(-1)


def _create_temporary_private_key_pem_path() -> str:
    """
    Create a temporary private key and path to the file.

    :return: private_key_pem_path
    """
    pem = _create_temporary_private_key()
    file = open(DEFAULT_PRIVATE_KEY_FILE, "wb")
    file.write(pem)
    file.close()
    return DEFAULT_PRIVATE_KEY_FILE
