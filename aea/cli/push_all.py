# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Push all available packages to a registry."""


from pathlib import Path
from typing import Dict, Optional, cast

import click

from aea.cli.packages import get_package_manager
from aea.cli.push import push_item_ipfs
from aea.cli.registry.settings import REGISTRY_REMOTE, REMOTE_IPFS
from aea.cli.utils.click_utils import registry_flag
from aea.cli.utils.config import get_default_remote_registry, load_item_config
from aea.configurations.constants import PACKAGES, PYCACHE
from aea.configurations.data_types import PackageId
from aea.package_manager.v0 import PackageManagerV0
from aea.package_manager.v1 import PackageManagerV1


@click.command("push-all")
@click.option(
    "--packages-dir", type=click.Path(file_okay=False, dir_okay=True, exists=True)
)
@click.option(
    "--retries",
    type=int,
    default=1,
    help="Tries on package push to the network.",
)
@registry_flag()
def push_all(packages_dir: Optional[Path], retries: int, registry: str) -> None:
    """Push all available packages to a registry."""
    try:
        push_all_packages(registry, packages_dir, retries=retries)
    except ValueError as e:
        raise click.ClickException(str(e)) from e


def push_all_packages(
    registry: str,
    packages_dir: Optional[Path] = None,
    package_type_config_class: Optional[Dict] = None,
    retries: int = 1,
) -> None:
    """Push all packages."""

    packages: Dict[PackageId, str]

    if registry != REGISTRY_REMOTE:
        raise click.ClickException(
            "Pushing all packages is not supported for the local registry."
        )

    if get_default_remote_registry() != REMOTE_IPFS:
        raise click.ClickException(
            "Pushing all packages is not supported for the HTTP registry."
        )

    if packages_dir is None:
        packages_dir = Path.cwd() / PACKAGES

    package_manager = get_package_manager(
        package_dir=packages_dir,
    )

    if isinstance(package_manager, PackageManagerV0):
        packages = cast(PackageManagerV0, package_manager).packages

    if isinstance(package_manager, PackageManagerV1):
        packages = cast(PackageManagerV1, package_manager).dev_packages

    for package_id in cast(Dict[PackageId, str], packages):
        package_path = package_manager.package_path_from_package_id(
            package_id=package_id,
        )
        if not package_path.is_dir() or package_path.name == PYCACHE:
            continue

        click.echo(f"Pushing: {package_path}")
        item_config = load_item_config(
            item_type=str(package_id.package_type),
            package_path=package_path,
            package_type_config_class=package_type_config_class,
        )
        push_item_ipfs(package_path, item_config.public_id, retries=retries)
        click.echo("")
