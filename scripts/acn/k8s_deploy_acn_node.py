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
"""Deploy an ACN libp2p node to a kubernetes cluster"""

import argparse
import base64
import os
import subprocess  # nosec
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type


SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

sys.path.append(SCRIPT_DIR)
from run_acn_node_standalone import (  # noqa # pylint: disable=wrong-import-position # isort:skip
    AcnNodeConfig,
)

# docker defaults
DOCKER_FETCHAI_DEFAULT_FILE = os.path.join(SCRIPT_DIR, "Dockerfile")
DOCKER_FETCHAI_DEFAULT_FILE_DEV = os.path.join(SCRIPT_DIR, "Dockerfile.dev")
DOCKER_FETCHAI_DEFAULT_CTX = SCRIPT_DIR
DOCKER_FETCHAI_DEFAULT_CTX_DEV = os.path.join(SCRIPT_DIR, "../../")
DOCKER_FETCHAI_DEFAULT_IMG = "acn_node"
DOCKER_FETCHAI_DEFAULT_REGISTRY = "gcr.io/fetch-ai-sandbox"

# k8s defaults
K8S_FETCHAI_DEFAULT_PUBLIC_HOST = "acn.fetch.ai"
K8S_FETCHAI_DEFAULT_PUBLIC_TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "k8s")
K8S_FETCHAI_DEFAULT_NAMESPACE = "agents-p2p-dht"


def _execute_cmd(cmd: List[str]) -> Tuple[str, bool]:
    """
    Run command as subprocess and wait for its termination

    :param cmd: command with arguments to execute
    :return: output of the command execution and execution success
    """

    print("-> Running: {}".format(cmd))
    proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)  # nosec
    out, _ = proc.communicate()
    success = False
    try:
        if proc.wait() == 0:
            success = True
    except (
        subprocess.CalledProcessError,  # pylint: disable=broad-except
        Exception,
    ) as e:
        print("_excute_cmd caught exception: {}".format(str(e)))
    print("-| Output :\n{}".format(out.decode("ascii")))
    return out.decode("ascii"), success


class DockerDeployment:
    """Build and Publish a Dockerfile"""

    def __init__(
        self, dockerfile: str, context: str, image: str, tag: str, registry: str
    ):
        """
        Initialize a DockerDeployment object

        :param dockerfile: path to the Dockerfile
        :param context: path to docker image context
        :param image: built image name
        :param tag: built image tag
        :param registry: registry to publish the image to
        """

        self.dockerfile = dockerfile
        self.context = context
        self.image = image
        self.tag = tag
        self.registry = registry

    def build_and_publish(self) -> bool:
        """
        Build the image and publich it to registry

        :return: success of the operation
        """

        cmds: List[List[str]] = list()

        cmds.append(
            [
                "docker",
                "build",
                "-t",
                "{}:{}".format(self.image, self.tag),
                "-f",
                self.dockerfile,
                self.context,
            ]
        )
        cmds.append(
            [
                "docker",
                "tag",
                "{}:{}".format(self.image, self.tag),
                "{}/{}:{}".format(self.registry, self.image, self.tag),
            ]
        )
        cmds.append(
            ["docker", "push", "{}/{}:{}".format(self.registry, self.image, self.tag)]
        )

        for cmd in cmds:
            _, ok = _execute_cmd(cmd)
            if not ok:
                return False

        return True


class K8sPodDeployment:
    """An application-agnostic deployment object"""

    def __init__(
        self,
        deployments_files: List[Path],
        docker_deployment: Optional[DockerDeployment],
    ):
        """
        Initialize a K8sPodDeployment object

        :param deployments_files: list of kubernetes yaml files to deploy
        :param docker_deployment: optional DockerDeployment to build and publish
        """
        self.deployment_files = deployments_files
        self.docker_deployment = docker_deployment

    def deploy(self) -> bool:
        """
        Deploy to k8s cluster

        :return: success of the operation
        """

        ok = True
        if self.docker_deployment:
            ok = self.docker_deployment.build_and_publish()
            if not ok:
                return ok
        for yaml in self.deployment_files:
            cmd = ["kubectl", "apply", "-f", str(yaml)]
            _, ok = _execute_cmd(cmd)
            if not ok:
                break
        return ok

    def delete(self) -> bool:
        """
        Delete deployment from k8s cluster

        :return: success of the operation
        """
        ok = True
        for yaml in self.deployment_files:
            cmd = ["kubectl", "delete", "-f", str(yaml)]
            _, ok = _execute_cmd(cmd)
            if not ok:
                break
        return ok


class AcnK8sPodConfig:
    """Store, parse, and generate kubernetes deployment for an ACN node"""

    K8S_DEPLOYMENT_NAME = "ph-deployment-name-here"
    K8S_NUMBER_OF_REPLICAS = "number-of-replicas"
    DEFAULT_K8S_NUMBER_OF_REPLICAS = 2
    K8S_NAMESPACE = "ph-deployment-namespace-here"
    K8S_PUBLIC_DNS = "ph-deployment-dns-here"

    DOCKER_IMAGE_REMOTE_WITH_TAG = "ph-gcr-image-with-tag-here"

    NODE_PORT = "ph-node-port-number-here"
    NODE_PORT_DELEGATE = "ph-node-delegate-port-number-here"
    NODE_PORT_MONITORING = "ph-node-monitoring-port-number-here"
    NODE_URI_EXTERNAL = "ph-node-external-uri-here"
    NODE_URI = "ph-node-local-uri-here"
    NODE_URI_DELEGATE = "ph-node-delegate-uri-here"
    NODE_URI_MONITORING = "ph-node-monitoring-uri-here"
    NODE_ENTRY_PEERS = "ph-node-entry-peers-list-here"
    NODE_KEY_NAME = "ph-node-priv-key-name-here"
    NODE_KEY_ENCODED = "ph-base64-encoded-private-key-here"
    NODE_LAST_ENTRY_PEER_HOST = "ph-latest-entry-peer-host-here"
    NODE_LAST_ENTRY_PEER_PORT = "ph-latest-entry-peer-port-here"
    NODE_LOG_FILE = "ph-node-log-file-path-here"
    # class defaults
    Defaults: Dict[str, str] = {
        K8S_DEPLOYMENT_NAME: "acn-node",
        NODE_LOG_FILE: "/acn_data/libp2p_node",
    }

    def __init__(
        self,
        acn_key_file: str,
        acn_port: int,
        acn_delegate_port: int,
        acn_monitoring_port: int,
        acn_entry_peers: Optional[List[str]],
        docker_file: str,
        docker_context: str,
        docker_image: str,
        docker_registry: str,
        k8s_public_hostname: str,
        k8s_namespace: str,
        k8s_template_files_dir: str,
        k8s_number_of_replicas: Optional[int],
        enable_checks: bool = True,
    ):
        """
        Initialize a AcnK8sPodConfig, populate the config dictionary

        :param acn_key_file: path to the acn node private key
        :param acn_port: acn node port number
        :param acn_delegate_port: acn node delegate service port number
        :param acn_monitoring_port: acn node monitoring service port number
        :param acn_entry_peers: optional list of acn node entry peers multiaddresses
        :param docker_file: path to Dockerfile
        :param docker_context: path to Dockerfile context
        :param docker_image: docker image name
        :param docker_registry: url of remote docker registry to push image to
        :param k8s_public_hostname: public dns for acn node's external uri
        :param k8s_namespace: k8s namespace to deploy node to
        :param k8s_template_files_dir: path to directory containing k8s yaml deployment templates
        :param enable_checks: enable configuration checks
        :param k8s_number_of_replicas: number of replica pods to run
        """

        config: Dict[str, str] = dict()
        cls: Type[AcnK8sPodConfig] = AcnK8sPodConfig

        k8s_number_of_replicas = (
            k8s_number_of_replicas or self.DEFAULT_K8S_NUMBER_OF_REPLICAS
        )

        # acn node configuration
        config[cls.NODE_KEY_NAME] = "node-priv-key-{}".format(acn_port)
        config[cls.NODE_PORT] = str(acn_port)
        config[cls.NODE_PORT_DELEGATE] = str(acn_delegate_port)
        config[cls.NODE_PORT_MONITORING] = str(acn_monitoring_port)
        config[cls.NODE_ENTRY_PEERS] = (
            ",".join(acn_entry_peers) if acn_entry_peers is not None else ""
        )
        config[cls.NODE_ENTRY_PEERS] = '"{}"'.format(config[cls.NODE_ENTRY_PEERS])
        peer_host, peer_port = cls._uri_from_multiaddr(
            acn_entry_peers[-1]
            if acn_entry_peers is not None and len(acn_entry_peers) > 0
            else ""
        )
        config[cls.NODE_LAST_ENTRY_PEER_HOST] = '"{}"'.format(peer_host)
        config[cls.NODE_LAST_ENTRY_PEER_PORT] = '"{}"'.format(peer_port)

        config[cls.NODE_URI] = "127.0.0.1:9000"
        config[cls.NODE_URI_DELEGATE] = "127.0.0.1:11000"
        config[cls.NODE_URI_MONITORING] = "127.0.0.1:8080"
        config[cls.NODE_URI_EXTERNAL] = "{}:{}".format(k8s_public_hostname, acn_port)
        config[cls.NODE_LOG_FILE] = '"{}_{}.log"'.format(
            cls.Defaults[cls.NODE_LOG_FILE], str(acn_port)
        )

        with open(acn_key_file, "r") as f:
            key = f.read().strip()
            config[cls.NODE_KEY_ENCODED] = base64.b64encode(key.encode("ascii")).decode(
                "ascii"
            )

        # k8s configuration
        config[cls.K8S_NUMBER_OF_REPLICAS] = str(k8s_number_of_replicas)
        config[cls.K8S_DEPLOYMENT_NAME] = "{}-{}".format(
            cls.Defaults[cls.K8S_DEPLOYMENT_NAME], str(acn_port)
        )
        config[cls.K8S_NAMESPACE] = k8s_namespace
        config[cls.K8S_PUBLIC_DNS] = k8s_public_hostname

        files: List[Path] = []
        for path in [
            Path(os.path.join(k8s_template_files_dir, p))
            for p in os.listdir(k8s_template_files_dir)
        ]:
            if path.is_file() and path.suffix == ".yaml":
                files.append(path)
        assert (
            len(files) > 0
        ), f"Couldn't find any template deployment file at {k8s_template_files_dir}"

        # docker configuration
        cmd = ["git", "describe", "--no-match", "--always", "--dirty"]
        docker_tag, ok = _execute_cmd(cmd)
        if not ok:
            docker_tag = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        else:
            docker_tag = docker_tag.strip()
        config[cls.DOCKER_IMAGE_REMOTE_WITH_TAG] = "{}/{}:{}".format(
            docker_registry, docker_image, docker_tag.strip()
        )

        self.config = config
        self.template_files = files
        self.docker_deployment = DockerDeployment(
            docker_file, docker_context, docker_image, docker_tag, docker_registry
        )

        if enable_checks:
            cls.check_config(self.config)

    @staticmethod
    def _uri_from_multiaddr(maddr: str) -> Tuple[str, str]:
        if maddr != "":
            parts = maddr.split("/")
            if len(parts) == 7:
                return parts[2], parts[4]
        return "", ""

    @staticmethod
    def check_config(config: Dict[str, str]) -> None:
        """
        Check an AcnK8sPodConfig deployment for correct configuration

        :param config: dictionary of configuration to check
        """
        AcnNodeConfig(
            base64.b64decode(
                config[AcnK8sPodConfig.NODE_KEY_ENCODED].encode("ascii")
            ).decode("ascii"),
            config[AcnK8sPodConfig.NODE_URI],
            config[AcnK8sPodConfig.NODE_URI_EXTERNAL],
            config[AcnK8sPodConfig.NODE_URI_DELEGATE],
            config[AcnK8sPodConfig.NODE_URI_MONITORING],
            config[AcnK8sPodConfig.NODE_ENTRY_PEERS].strip('"').split(","),
            "",
            True,
        )

    def generate_deployment(self) -> K8sPodDeployment:
        """
        Generate deployment for the current configuration

        :return: deployment object
        """

        deployment_file = ".acn_deployment.yaml"
        out = open(deployment_file, "w")

        for path in self.template_files:
            with open(path, "r") as f:
                content = f.read()

            for placeholder, value in self.config.items():
                content = content.replace(placeholder, value)

            out.write(content)
            out.write("\n---\n")

        out.close()

        return K8sPodDeployment([Path(deployment_file)], self.docker_deployment)


def parse_commandline():
    """Parse script cl arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file",
        action="store",
        type=str,
        dest="from_file",
        required=False,
        help="Use previously generated deployment",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        dest="delete_deployment",
        required=False,
        help="Delete an already deployed node with the same configuration",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        dest="generate_only",
        required=False,
        help="Don't deploy the generated yaml file",
    )
    parser.add_argument(
        "--acn-key-file",
        action="store",
        type=str,
        dest="key",
        required=False,
        help="acn node's private key file",
    )
    parser.add_argument(
        "--acn-port",
        action="store",
        type=int,
        dest="port",
        required=False,
        help="acn node's external port number. Internal is 9000",
    )
    parser.add_argument(
        "--acn-port-delegate",
        action="store",
        type=int,
        dest="delegate_port",
        required=False,
        help="acn node's delegate external service port number. Internal is 11000",
    )
    parser.add_argument(
        "--acn-port-monitoring",
        action="store",
        type=int,
        dest="monitoring_port",
        required=False,
        default=8080,
        help="acn node's monitoring service port number (local only)",
    )
    parser.add_argument(
        "--acn-entry-peers-maddrs",
        action="store",
        nargs="*",
        dest="entry_peers_maddrs",
        help="acn node's entry peers in libp2p multiaddress format",
    )
    parser.add_argument(
        "--k8s-fetchai-defaults",
        action="store_true",
        dest="k8s_fetchai_defaults",
        required=False,
        help="Use FetchAI defaults for k8s configuration",
    )
    parser.add_argument(
        "--k8s-public-hostname",
        action="store",
        type=str,
        dest="k8s_public_hostname",
        required=False,
        help="K8s public hostname to use for acn node's external uri",
    )
    parser.add_argument(
        "--k8s-namespace",
        action="store",
        type=str,
        dest="k8s_namespace",
        required=False,
        help="K8s deployment namespace",
    )
    parser.add_argument(
        "--k8s-template-files-dir",
        action="store",
        type=str,
        dest="k8s_template_files_dir",
        required=False,
        help="Directory containing k8s template yaml deployment files",
    )

    parser.add_argument(
        "--docker-fetchai-defaults",
        action="store_true",
        dest="docker_fetchai_defaults",
        required=False,
        help="Use FetchAI defaults for docker configuration",
    )
    parser.add_argument(
        "--docker-fetchai-defaults-dev",
        action="store_true",
        dest="docker_fetchai_defaults_dev",
        required=False,
        help="Use FetchAI Dev defaults for docker configuration",
    )
    parser.add_argument(
        "--docker-file",
        action="store",
        type=str,
        dest="docker_file",
        required=False,
        help="Path to Dockerfile to build",
    )
    parser.add_argument(
        "--docker-ctx",
        action="store",
        type=str,
        dest="docker_ctx",
        required=False,
        help="Path to Dockerfile context",
    )
    parser.add_argument(
        "--docker-image",
        action="store",
        type=str,
        dest="docker_image",
        required=False,
        help="Docker image name",
    )
    parser.add_argument(
        "--docker-registry",
        action="store",
        type=str,
        dest="docker_registry",
        required=False,
        help="Docker remote registry",
    )

    parser.add_argument(
        "--number-of-replicas",
        action="store",
        type=int,
        dest="number_of_replicas",
        required=False,
        help="Number of replicas",
    )

    args = parser.parse_args()

    # checks
    if args.from_file is None and (
        args.key is None
        or args.port is None
        or args.delegate_port is None
        or args.monitoring_port is None
    ):
        parser.error(
            "--acn-key-file, --acn-port, --acn-port-delegate, --acn-port-monitoring are required when --from-file is not used"
        )

    if (
        not args.from_file
        and not args.k8s_fetchai_defaults
        and (
            args.k8s_public_hostname is None
            or args.k8s_namespace is None
            or args.k8s_template_files_dir is None
        )
    ):
        parser.error(
            "--k8s-public-hostname, --k8s-namespace, --k8s-template-files-dir are required when --k8s-fetchai-defaults is not set"
        )

    if (
        not args.from_file
        and not args.docker_fetchai_defaults
        and not args.docker_fetchai_defaults_dev
        and (
            args.docker_file is None
            or args.docker_ctx is None
            or args.docker_image is None
            or args.docker_registry is None
        )
    ):
        parser.error(
            "--docker-file, --docker-ctx, --docker-image, --docker-registry are required when --docker-fetchai-defaults[-dev] is not set"
        )

    if args.docker_fetchai_defaults and args.docker_fetchai_defaults_dev:
        parser.error(
            "--docker-fetchai-defaults and --docker-fetchai-defaults-dev are mutually exclusive"
        )

    if args.generate_only and (args.delete_deployment or args.from_file):
        parser.error("--generate-only can not be used with --delete or --from-file")

    return args


def main():
    """K8s deploy acn node"""

    args = parse_commandline()

    pod_deployment: Optional[K8sPodDeployment] = None

    if args.from_file:
        pod_deployment = K8sPodDeployment([Path(args.from_file)], None)
    else:
        dargs: List[Any] = [
            args.key,
            args.port,
            args.delegate_port,
            args.monitoring_port,
        ]

        dargs.append(
            args.entry_peers_maddrs if args.entry_peers_maddrs is not None else ""
        )

        docker_config: List[str] = []
        if args.docker_fetchai_defaults_dev:
            docker_config = [
                DOCKER_FETCHAI_DEFAULT_FILE_DEV,
                DOCKER_FETCHAI_DEFAULT_CTX_DEV,
                DOCKER_FETCHAI_DEFAULT_IMG,
                DOCKER_FETCHAI_DEFAULT_REGISTRY,
            ]
        elif args.docker_fetchai_defaults:
            docker_config = [
                DOCKER_FETCHAI_DEFAULT_FILE,
                DOCKER_FETCHAI_DEFAULT_CTX,
                DOCKER_FETCHAI_DEFAULT_IMG,
                DOCKER_FETCHAI_DEFAULT_REGISTRY,
            ]
        if args.docker_file is not None:
            docker_config[0] = args.docker_file
        if args.docker_ctx is not None:
            docker_config[1] = args.docker_ctx
        if args.docker_image is not None:
            docker_config[2] = args.docker_image
        if args.docker_registry is not None:
            docker_config[3] = args.docker_registry

        dargs.extend(docker_config)

        k8s_config: List[str] = []
        if args.k8s_fetchai_defaults:
            k8s_config = [
                K8S_FETCHAI_DEFAULT_PUBLIC_HOST,
                K8S_FETCHAI_DEFAULT_NAMESPACE,
                K8S_FETCHAI_DEFAULT_PUBLIC_TEMPLATE_DIR,
            ]
        if args.k8s_public_hostname is not None:
            k8s_config[0] = args.k8s_public_hostname
        if args.k8s_namespace is not None:
            k8s_config[1] = args.k8s_namespace
        if args.k8s_template_files_dir is not None:
            k8s_config[2] = args.k8s_template_files_dir

        dargs.extend(k8s_config)

        pod_deployment = AcnK8sPodConfig(
            dargs[0],
            dargs[1],
            dargs[2],
            dargs[3],
            dargs[4],
            dargs[5],
            dargs[6],
            dargs[7],
            dargs[8],
            dargs[9],
            dargs[10],
            dargs[11],
            k8s_number_of_replicas=args.number_of_replicas,
        ).generate_deployment()

    if args.generate_only:
        return

    try:
        if args.delete_deployment:
            pod_deployment.delete()
        else:
            pod_deployment.deploy()
    except Exception as e:
        raise e


if __name__ == "__main__":
    main()
