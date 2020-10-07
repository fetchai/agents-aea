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
""" Deploy an ACN libp2p node to a kubernetes cluster """

import argparse
import base64
import os
import subprocess  # nosec
from os import stat
from pathlib import Path
from tempfile import mkdtemp
from typing import Dict, List, Optional, Tuple, Type, Union

from .run_acn_node_standalone import AcnNodeConfig

k8s_deployment_name = "ph-deployment-name-here"
k8s_cluster_namespace = "ph-cluster-namespace-here"
k8s_check_listening_host = "ph-latest-entry-peer-host-here"
k8s_check_listening_port = "ph-latest-entry-peer-port-here"
k8s_docker_image_url = "ph-gcr-image-with-tag-here"
k8s_docker_container_name = "ph-container-name-here"
k8s_dnsname = "ph-dnsname-here"
k8s_dnsname_target = "ph-dnsname-target-here"

node_port_number = "ph-node-port-number-here"
node_port_number_delegate = "ph-node-delegate-port-number-here"
node_private_key = "ph-node-priv-key-name-here"
node_uri_external = "ph-node-external-uri-here"
node_uri = "ph-node-local-uri-here"
node_uri_delegate = "ph-node-delegate-uri-here"
node_entry_peers = "ph-node-entry-peers-list-here"
node_key_name = "ph-node-priv-key-name-here"
node_key_encoded = "ph-base64-encoded-private-key-here"

def _execute_cmd(cmd: List[str]) -> str:
    proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)  # nosec
    out, _ = proc.communicate()
    try:
        proc.wait()
    except:
        pass
    return out.decode('ascii')

class K8sPodDeployment:
    """ """

    def __init__(
        self,
        root_dir: str,
        deployments_files: List[Path],
        dockerfile_path: Union[Path, str],
        docker_remote_image: str,
    ):
        """
        """

        self.deployment_files = deployments_files
        self.dockerfile = dockerfile_path
        self.docker_remote_image = docker_remote_image
        self.root_dir = root_dir

    @property
    def yaml_files(self) -> List[Path]:
        return self.deployment_files

    @property
    def dockerfile(self) -> Path:
        return Path(self.dockerfile)

    @property
    def docker_remote_image(self) -> str:
        return self.docker_remote_image


class AcnK8sPodConfig:
    """
    Store, parse, and generate kubernetes deployment for ACN node
    """

    K8S_DEPLOYMENT_NAME = "ph-deployment-name-here"
    K8S_PUBLIC_DNS = "agents-p2p-dht.sandbox.fetch-ai.com"  # TODO

    DOCKER_IMAGE_REMOTE_WITH_TAG = "ph-gcr-image-with-tag-here"

    NODE_PORT = "ph-node-port-number-here"
    NODE_PORT_DELEGATE = "ph-node-delegate-port-number-here"
    NODE_PORT_MONITORING = "ph-node-monitoring-port-number-here"  # TODO
    NODE_URI_EXTERNAL = "ph-node-external-uri-here"
    NODE_URI = "ph-node-local-uri-here"
    NODE_URI_DELEGATE = "ph-node-delegate-uri-here"
    NODE_URI_MONITORING = "ph-node-monitoring-uri-here"
    NODE_ENTRY_PEERS = "ph-node-entry-peers-list-here"
    NODE_KEY_NAME = "ph-node-priv-key-name-here"
    NODE_KEY_ENCODED = "ph-base64-encoded-private-key-here"
    NODE_LAST_ENTRY_PEER_HOST = "ph-latest-entry-peer-host-here"
    NODE_LAST_ENTRY_PEER_PORT = "ph-latest-entry-peer-port-here"

    # TODO add the rest of placeholders

    Defaults: Dict[str, str] = {
        K8S_DEPLOYMENT_NAME: "agents-p2p-dht",
        K8S_PUBLIC_DNS: "agents-p2p-dht.sandbox.fetch-ai.com",
        DOCKER_IMAGE_REMOTE_WITH_TAG: "gcr.io/fetch-ai-sandbox/agents-p2p-dht",
    }

    def __init__(
        self,
        root_dir: str,
        key_file: str,
        port: int,
        delegate_port: int,
        monitoring_port: int,
        entry_peers: Optional[List[str]],
        enable_checks: bool = True,
        dnsname: Optional[str] = None,
    ):
        """
        Initialize a AcnK8sPodConfig, populate the config dict  

        :param :
        """

        config: Dict[str, str] = dict()
        cls: Type[AcnK8sPodConfig] = AcnK8sPodConfig

        config[cls.K8S_DEPLOYMENT_NAME] = "{}-{}".format(
            cls.Defaults[cls.K8S_DEPLOYMENT_NAME], str(port)
        )
        config[cls.K8S_PUBLIC_DNS] = (
            dnsname if dnsname is not None else cls.Defaults[cls.K8S_PUBLIC_DNS]
        )

        config[cls.DOCKER_IMAGE_REMOTE_WITH_TAG] = cls.Defaults[
            cls.DOCKER_IMAGE_REMOTE_WITH_TAG
        ]

        config[cls.NODE_PORT] = port
        config[cls.NODE_PORT_DELEGATE] = delegate_port
        config[cls.NODE_PORT_MONITORING] = monitoring_port
        config[cls.NODE_ENTRY_PEERS] = (
            ",".join(entry_peers) if entry_peers is not None else ""
        )
        peer_host, peer_port = cls._parse_multiaddr_for_uri(
            entry_peers[-1] if entry_peers is not None and len(entry_peers) > 0 else ""
        )
        config[cls.NODE_LAST_ENTRY_PEER_HOST] = peer_host
        config[cls.NODE_LAST_ENTRY_PEER_PORT] = peer_port

        config[cls.NODE_URI] = "0.0.0.0:{}".format(port)
        config[cls.NODE_URI_DELEGATE] = "0.0.0.0:{}".format(delegate_port)
        config[cls.NODE_URI_MONITORING] = "0.0.0.0:{}".format(monitoring_port)
        config[cls.NODE_URI_EXTERNAL] = "{}:{}".format(
            dnsname if dnsname is not None else cls.Defaults[cls.K8S_PUBLIC_DNS], port
        )

        with open(key_file, "r") as f:
            key = f.read().strip()
            config[cls.NODE_KEY_ENCODED] = base64.b64encode(key.encode("ascii")).decode(
                "ascii"
            )

        files: List[Path] = []
        for path in [Path(p) for p in os.listdir(root_dir)]:
            if path.is_file(path) and path.suffix == ".yaml":
                files.append(path)
        assert (
            len(files) > 0
        ), f"Couldn't find any template deployment file at {root_dir}"

        self.config = config
        self.template_files = files
        self.dockerfile = root_dir / "Dockerfile"

        if enable_checks:
            cls._check_config(self.config)

    @staticmethod
    def _parse_multiaddr_for_uri(maddr: str) -> Tuple[str, str]:
        if maddr != "":
            parts = maddr.split("/")
            if len(parts) == 7:
                return parts[3], parts[5]
        return "", ""

    @staticmethod
    def check_config(config: Dict[str, str]) -> None:
        AcnNodeConfig(
            base64.b64decode(
                config[AcnK8sPodConfig.NODE_KEY_ENCODED].encode("ascii")
            ).decode("ascii"),
            config[AcnK8sPodConfig.NODE_URI],
            config[AcnK8sPodConfig.NODE_URI_EXTERNAL],
            config[AcnK8sPodConfig.NODE_URI_DELEGATE],
            config[AcnK8sPodConfig.NODE_URI_MONITORING],
            config[AcnK8sPodConfig.NODE_ENTRY_PEERS],
            True,
        )

    def generate_deployment(self) -> K8sPodDeployment:
        """ 
        """

        workdir = mkdtemp()
        deployment_files: List[Path] = []

        for path in self.template_files:
            with open(path, "r") as f:
                content = f.read()

            for placeholder, value in self.config.items():
                content = content.replace(placeholder, value)

            with open(workdir / path.name, "w") as f:
                f.write(content)
            
            deployment_files.append(workdir / path.name)

        tag = _execute_cmd(["git", "describe", "--no-match", "--always", "--dirty"])
        

        return K8sPodDeployment(workdir, deployment_files, self.dockerfile, "{}:{}".format(config[AcnK8sPodConfig.DOCKER_IMAGE_REMOTE_WITH_TAG]))


def parse_commandline():
    """ Parse script cl arguments """

    # args:
    # - scripts absolute path
    # - private key file
    # - port number / uri
    # |__-> deployment name
    # - delegate port number
    # - entry peers list

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--key-file",
        action="store",
        type=str,
        dest="key",
        help="node's private key file",
    )
    parser.add_argument(
        "--port",
        action="store",
        type=str,
        dest="port",
        help="node's port number (both local and external)",
    )
    parser.add_argument(
        "--port-delegate",
        action="store",
        type=str,
        dest="delegate_port",
        required=False,
        help="node's delegate service port number (both local and external)",
    )
    parser.add_argument(
        "--entry-peers-maddrs",
        action="store",
        nargs="*",
        dest="entry_peers_maddrs",
        help="node's entry peers in libp2p multiaddress format",
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":

    args = parse_commandline()
