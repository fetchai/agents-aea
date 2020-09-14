#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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

import os
import subprocess
import argparse
from typing import Dict, List, Optional

from multihash import decode as multihashdecode
from ecdsa import SigningKey, curves
from base58 import b58decode
from binascii import unhexlify


class AcnNodeConfig:
    """
    """

    KEY = "AEA_P2P_ID"
    URI = "AEA_P2P_URI"
    EXTERNAL_URI = "AEA_P2P_URI_PUBLIC"
    DELEGATE_URI = "AEA_P2P_DELEGATE_URI"
    ENTRY_PEERS_MADDRS = "AEA_P2P_ENTRY_URIS"
    IPC_IN = "AEA_TO_NODE"
    IPC_OUT = "NODE_TO_AEA"
    AEA_ADDRESS = "AEA_AGENT_ADDR"
    LIST_SEPARATOR = ","

    def __init__(
        self,
        key: str,
        uri: str,
        external_uri: Optional[str] = None,
        delegate_uri: Optional[str] = None,
        entry_peers_maddrs: Optional[List[str]] = None,
        enable_checks: bool = True,
    ):
        self.config: Dict[str, str] = dict()

        self.config[AcnNodeConfig.KEY] = key
        self.config[AcnNodeConfig.URI] = uri
        self.config[AcnNodeConfig.EXTERNAL_URI] = (
            external_uri if external_uri is not None else ""
        )
        self.config[AcnNodeConfig.DELEGATE_URI] = (
            delegate_uri if delegate_uri is not None else ""
        )

        entry_peers_maddrs_list = (
            AcnNodeConfig.LIST_SEPARATOR.join(entry_peers_maddrs)
            if entry_peers_maddrs is not None
            else ""
        )
        self.config[AcnNodeConfig.ENTRY_PEERS_MADDRS] = entry_peers_maddrs_list

        self.config[AcnNodeConfig.AEA_ADDRESS] = ""
        self.config[AcnNodeConfig.IPC_IN] = ""
        self.config[AcnNodeConfig.IPC_OUT] = ""

        if enable_checks:
            AcnNodeConfig.check_config(self.config)

    def dump(self, file_path: str) -> None:
        """ Write current configuration to file """
        with open(file_path, "w") as f:
            for key, value in self.config.items():
                f.write("{}={}\n".format(key, value))

    @classmethod
    def from_file(cls, file_path: str, enable_checks: bool = True) -> "AcnNodeConfig":
        """
        Create a new AcnNodeConfig objet from file
        
        :param file_path: path to the file containing the configuration
        :return: newly created AcnNodeConfig object, if successful
        """

        lines: List[str] = list()
        with open(file_path, "r") as f:
            lines = f.readlines()

        config = dict()
        for nbr, line in enumerate(lines):
            parts = line.strip().split("=")
            if len(parts) != 2:
                raise ValueError(
                    "Malformed configuration line {}: {}".format(nbr + 1, line)
                )
            config[parts[0]] = parts[1]

        key = config[AcnNodeConfig.KEY]
        uri = config[AcnNodeConfig.URI]
        external_uri = config.get(AcnNodeConfig.EXTERNAL_URI, None)
        delegate_uri = config.get(AcnNodeConfig.DELEGATE_URI, None)
        entry_peers = config.get(AcnNodeConfig.ENTRY_PEERS_MADDRS, None)

        return cls(key, uri, external_uri, delegate_uri, entry_peers, enable_checks)

    @staticmethod
    def check_config(config: Dict[str, str]) -> None:
        """
        Validate an ACN node configuration
        
        :param config: dictionary containing the configuration to check
        """

        SigningKey.from_string(
            unhexlify(config[AcnNodeConfig.KEY]), curve=curves.SECP256k1
        )

        AcnNodeConfig._check_uri(config[AcnNodeConfig.URI])
        if config[AcnNodeConfig.EXTERNAL_URI] != "":
            AcnNodeConfig._check_uri(config[AcnNodeConfig.EXTERNAL_URI])
        if config[AcnNodeConfig.DELEGATE_URI] != "":
            AcnNodeConfig._check_uri(config[AcnNodeConfig.DELEGATE_URI])

        maddrs = config[AcnNodeConfig.ENTRY_PEERS_MADDRS].split(
            AcnNodeConfig.LIST_SEPARATOR
        )
        for maddr in maddrs:
            AcnNodeConfig._check_maddr(maddr)

    @staticmethod
    def _check_uri(uri: str) -> None:
        if uri == "":
            return
        parts = uri.split(":")
        if len(parts) != 2:
            raise ValueError("Malformed uri '{}'".format(uri))
        int(parts[1])

    @staticmethod
    def _check_maddr(maddr: str) -> None:
        if maddr == "":
            return
        parts = maddr.split("/")
        if len(parts) != 7:
            raise ValueError("Malformed multiaddress '{}'".format(maddr))
        multihashdecode(b58decode(parts[-1]))


class AcnNodeStandalone:
    """
    """

    def __init__(self, config: AcnNodeConfig, libp2p_node_binary: str):
        """
        Initialize a new AcnNodeStandalone object

        :param config: node's configuration
        :param libp2p_node_binary: path to libp2p node binary
        """

        self.config = config
        self.binary = libp2p_node_binary
        self._proc = None  # type: Optional[subprocess.Popen]

    def run(self):
        """ """

        config_file = ".acn_config"
        self.config.dump(config_file)

        cmd = [self.binary, config_file]

        self._proc = subprocess.Popen(cmd, shell=False,)  # nosec

        try:
            self._proc.wait()
        except KeyboardInterrupt:
            pass

    def stop(self):
        """ """

        if self._proc is not None:
            self._proc.terminate()
            self._proc.wait()


def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument("libp2p_node")
    config = parser.add_mutually_exclusive_group(required=False)
    config.add_argument(
        "--config-from-env",
        action="store_true",
        dest="config_from_env",
        help="get node configuration from environment variables",
    )
    config.add_argument(
        "--config-from-file",
        action="store",
        type=str,
        dest="config_from_file",
        help="node configuration file",
    )

    parser.add_argument(
        "--key-file",
        action="store",
        type=str,
        dest="key",
        # required=True,
        help="node's private key file",
    )
    parser.add_argument(
        "--uri",
        action="store",
        type=str,
        dest="uri",
        # required=True,
        help="node's local uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--uri-external",
        action="store",
        type=str,
        dest="external_uri",
        required=False,
        help="node's external uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--uri-delegate",
        action="store",
        type=str,
        dest="delegate_uri",
        required=False,
        help="node's delegate service uri in format {ip_address:port}",
    )
    parser.add_argument(
        "--entry-peers-maddrs",
        action="store",
        nargs="*",
        dest="entry_peers_maddrs",
        help="node's entry peer uri in libp2p multiaddress fromat",
    )

    args = parser.parse_args()

    if (
        args.config_from_env is False
        and args.config_from_file is None
        and (args.key is None or args.uri is None)
    ):
        parser.error(
            "--key-file and --uri are required when configuration is not passed through env or file"
        )

    return args


if __name__ == "__main__":

    args = parse_commandline()

    node_config: Optional[AcnNodeConfig] = None

    if args.config_from_env:
        key = os.environ[AcnNodeConfig.KEY]
        uri = os.environ[AcnNodeConfig.URI]
        external_uri = os.environ.get(AcnNodeConfig.EXTERNAL_URI)
        delegate_uri = os.environ.get(AcnNodeConfig.DELEGATE_URI)
        entry_peers = os.environ.get(AcnNodeConfig.ENTRY_PEERS_MADDRS)
        entry_peers_list = entry_peers.split(",") if entry_peers is not None else []
        node_config = AcnNodeConfig(
            key, uri, external_uri, delegate_uri, entry_peers_list
        )

    elif args.config_from_file is not None:
        node_config = AcnNodeConfig.from_file(args.config_from_file)

    else:
        print("Config from argsssssssssssss")
        with open(args.key, "r") as f:
            key = f.read().strip()
        node_config = AcnNodeConfig(
            key, args.uri, args.external_uri, args.delegate_uri, args.entry_peers_maddrs
        )

    node = AcnNodeStandalone(node_config, args.libp2p_node)
    try:
        node.run()
    except Exception:
        node.stop()
        raise

###    if args.priv is not None:
###        priv = FetchAICrypto(args.priv)
###    else:
###        priv = FetchAICrypto()
###
###    # uri (host & port)
###    uri = None
###    uri_from_env = os.environ.get("NODE_LOCAL_URI")
###    if uri_from_env is not None:
###        uri = Uri(uri_from_env)
###    else:
###        uri = Uri(args.uri)
###
###    # external uri (host & port)
###    external_uri = None
###    public_uri_from_env = os.environ.get("NODE_PUBLIC_URI")
###    if public_uri_from_env is not None:
###        public_uri = Uri(public_uri_from_env)
###    elif args.public_uri is not None:
###        public_uri = Uri(args.public_uri)
###
###    # delegate uri (host & port)
###    delegate_uri = None
###    delegate_uri_from_env = os.environ.get("NODE_DELEGATE_URI")
###    if delegate_uri_from_env is not None:
###        delegate_uri = Uri(delegate_uri_from_env)
###    elif args.delegate_uri is not None:
###        delegate_uri = Uri(args.delegate_uri)
###
###    # entry peers, optional
###    entry_peers = list()
###    entry_peers_from_env = os.environ.get("NODE_ENTRY_PEERS")
###    if entry_peers_from_env is not None:
###        entry_peers = [
###            MultiAddr(maddr)
###            for maddr in list(filter(None, entry_peers_from_env.split(",")))
###        ]
###    elif args.entry_peers_maddrs is not None:
###        entry_peers = [MultiAddr(maddr) for maddr in args.entry_peers_maddrs]
###
###    # peers to send messages to
###    peers_pubs = list()
###    if args.peers_ids_file is not None:
###        with open(args.peers_ids_file, "r") as f:
###            peers_pubs = [line.strip() for line in f.readlines()]
###
###    # number of messages to send to each peer
###    nbr_msgs = 0
###    if args.nbr_msgs is not None:
###        nbr_msgs = args.nbr_msgs
###
###    # node key pair
###    key_from_env = os.environ.get("NODE_PRIV_KEY")
###    node_key_file = "{}/key.txt".format(tempfile.mkdtemp())
###    if key_from_env is not None:
###        with open(node_key_file, "w") as f:
###            f.write(key_from_env)
###    elif args.priv_node is not None:
###        with open(node_key_file, "wb") as f:
###            FetchAICrypto(args.priv_node).dump(f)
###    else:
###        with open(node_key_file, "wb") as f:
###            FetchAICrypto().dump(f)
###
###    # run the connection
###    runP2PLibp2pConnectionWithinMultiplexer(
###        node_key_file, uri, entry_peers, peers_pubs, nbr_msgs, public_uri, delegate_uri
###    )
###
