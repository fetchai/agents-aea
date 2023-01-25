# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Implementation of the 'aea test' command."""
import contextlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Set, Tuple, Union, cast

import click
import pytest
from coverage.cmdline import main as coverage

from aea.aea_builder import AEABuilder
from aea.cli.utils.click_utils import (
    PublicIdParameter,
    determine_package_type_for_directory,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import get_package_path
from aea.components.base import load_aea_package, perform_load_aea_package
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    PackageConfiguration,
)
from aea.configurations.constants import (
    AEA_TEST_DIRNAME,
    CONNECTION,
    CONTRACT,
    PROTOCOL,
    SKILL,
)
from aea.configurations.data_types import (
    ComponentId,
    ComponentType,
    PackageType,
    PublicId,
)
from aea.configurations.loader import (
    load_component_configuration,
    load_package_configuration,
)
from aea.configurations.manager import find_component_directory_from_component_id
from aea.exceptions import enforce
from aea.package_manager.v1 import PackageManagerV1


COVERAGERC_FILE = ".coveragerc"
COVERAGERC_CONFIG = """[run]
omit =
    */tests/*
    */.tox/*
    */*_pb2.py
    */*_pb2_*.py

[html]
directory = {root_dir}/htmlcov

[xml]
output = {root_dir}/coverage.xml
"""


@click.group(
    invoke_without_command=True,
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
@click.option(
    "--cov",
    is_flag=True,
    default=False,
    help="Use this flag to enable code coverage checks.",
)
@click.option(
    "--cov-output",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Directory to output codecov reports.",
)
@click.option(
    "--append",
    help="Directory to output codecov reports.",
    is_flag=True,
)
def test(
    click_context: click.Context, cov: bool, cov_output: str, append: bool
) -> None:
    """Run tests of an AEA project."""
    ctx = cast(Context, click_context.obj)
    ctx.config["cov"] = cov
    ctx.config["cov_output"] = cov_output
    ctx.config["append"] = append

    if click_context.invoked_subcommand is None:
        test_aea_project(click_context, Path(ctx.cwd), args=[])


@check_aea_project
def test_aea_project(
    click_context: click.Context, aea_project_dirpath: Path, args: Sequence[str]
) -> None:
    """Run tests of an AEA project."""
    click.echo("Executing tests of the AEA project...")
    ctx = cast(Context, click_context.obj)
    test_package_by_path(
        aea_project_dirpath,
        args,
        aea_project_path=Path(ctx.cwd),
        skip_consistency_check=ctx.config.get("skip_consistency_check", False),
    )


@test.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def connection(
    click_context: click.Context,
    connection_public_id: PublicId,
) -> None:
    """Executes a test suite of a connection package dependency."""
    test_item(click_context.obj, CONNECTION, connection_public_id, click_context.args)


@test.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def contract(
    click_context: click.Context,
    contract_public_id: PublicId,
) -> None:
    """Executes a test suite of a contract package dependency."""
    test_item(click_context.obj, CONTRACT, contract_public_id, click_context.args)


@test.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def protocol(
    click_context: click.Context,
    protocol_public_id: PublicId,
) -> None:
    """Executes a test suite of a protocol package dependency."""
    test_item(click_context.obj, PROTOCOL, protocol_public_id, click_context.args)


@test.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def skill(
    click_context: click.Context,
    skill_public_id: PublicId,
) -> None:
    """Executes a test suite of a skill package dependency."""
    test_item(click_context.obj, SKILL, skill_public_id, click_context.args)


@test.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument(
    "path", type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True
)
@click.pass_context
def by_path(
    click_context: click.Context,
    path: str,
) -> None:
    """Executes a test suite of a package specified by a path."""
    click.echo(f"Executing tests of package at {path}'...")

    ctx: Context = click_context.obj
    full_path = Path(ctx.cwd) / Path(path)

    test_package_by_path(
        full_path,
        click_context.args,
        packages_dir=Path(ctx.registry_path),
        cov=ctx.config.get("cov", False),
        cov_output=ctx.config.get("cov_output"),
        append_coverage=ctx.config.get("append", False),
        skip_consistency_check=ctx.config.get("skip_consistency_check", False),
    )


@test.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.option(
    "--author",
    "-a",
    type=str,
    multiple=True,
    help="Author name(s) to restrict tests to.",
)
@click.option(
    "--all",
    "all_",
    is_flag=True,
    show_default=True,
    default=False,
    help="Run test for all packages. By default dev only.",
)
@click.pass_context
def packages(click_context: click.Context, author: Tuple[str], all_: bool) -> None:
    """Executes a test suite for a collection of packages."""
    ctx: Context = click_context.obj
    packages_dir = Path(ctx.registry_path)
    available_packages = get_packages_list(
        packages_dir=packages_dir, packages_filter="all" if all_ else "dev"
    )

    cov = ctx.config.get("cov", False)
    cov_output = Path(ctx.config.get("cov_output") or Path.cwd()).resolve()

    with CoverageContext(root_dir=cov_output, append=True) as coverage_context:
        failures = test_package_collection(
            available_packages=available_packages,
            packages_dir=packages_dir,
            pytest_args=click_context.args,
            cov=cov,
            coverage_context=coverage_context,
            authors=author,
        )
        if cov:
            coverage_context.generate()

    if len(failures) > 0:
        click.echo("Failed tests")
        click.echo("Exit Code\tPackage")
        for exit_code, package in failures:
            click.echo(f"{exit_code}       \t{package}")
        sys.exit(1)


def get_packages_list(
    packages_dir: Path, packages_filter: str = "dev"
) -> List[Tuple[str, Path]]:
    """
    Get list of packages to test.

    :param packages_dir: Path
    :param packages_filter: str, ["all", "dev"]

    :return: List of tuples of pacakge type and path
    """
    package_manager = PackageManagerV1.from_dir(packages_dir)
    if packages_filter == "all":
        packages_ids = package_manager.all_packages.keys()
    elif packages_filter == "dev":
        packages_ids = package_manager.dev_packages.keys()
    else:
        raise ValueError(
            f"Unknown package filter: {packages_filter}. Valid are all,dev"
        )

    packages_list = [
        (
            str(package_id.package_type.to_plural()),
            package_manager.package_path_from_package_id(package_id),
        )
        for package_id in packages_ids
    ]
    return packages_list


class CoverageContext:
    """Coveragerc file context"""

    def __init__(
        self,
        root_dir: Path,
        append: bool = False,
    ) -> None:
        """Initialize object."""

        self.root_dir = root_dir
        self.append = append

        self._t = tempfile.TemporaryDirectory()
        self.coveragerc_file = Path(self._t.name, COVERAGERC_FILE)

    def pytest_args(
        self,
        test_path: Path,
    ) -> List[str]:
        """Returns coverage flags for pytest command"""

        args = [
            f"--cov-config={self.coveragerc_file}",
            "--cov-report=term",
            f"--cov={test_path}",
        ]

        if self.append:
            args.append("--cov-append")
        return args

    def __enter__(
        self,
    ) -> "CoverageContext":
        """Enter context."""
        self.coveragerc_file.write_text(
            COVERAGERC_CONFIG.format(root_dir=self.root_dir),
        )
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit context."""

        with contextlib.suppress(OSError, PermissionError):
            self._t.cleanup()

    def generate(
        self,
    ) -> None:
        """Generate coverage report."""

        coverage(argv=["html", f"--rcfile={self.coveragerc_file}"])
        coverage(argv=["xml", f"--rcfile={self.coveragerc_file}"])


def test_item(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    pytest_arguments: Sequence[str],
) -> None:
    """
    Run tests of a package dependency.

    :param ctx: the context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param pytest_arguments: arguments to forward to Pytest
    """
    click.echo(
        "Executing tests of component of type {}, {}' ...".format(
            item_type, item_public_id
        )
    )
    package_dirpath = Path(
        get_package_path(ctx.cwd, item_type, item_public_id, is_vendor=False)
    )
    if not package_dirpath.exists():
        # check if it is a vendor package
        package_dirpath = Path(
            get_package_path(ctx.cwd, item_type, item_public_id, is_vendor=True)
        )
        enforce(
            package_dirpath.exists(),
            exception_text=f"package {item_public_id} of type {item_type} not found",
            exception_class=click.ClickException,
        )
    # for a package in an AEA project, the "packages" dir is the AEA project dir
    aea_project_path = Path(ctx.cwd)
    test_package_by_path(
        package_dirpath,
        pytest_arguments,
        aea_project_path=aea_project_path,
        cov=ctx.config.get("cov", False),
        skip_consistency_check=ctx.config.get("skip_consistency_check", False),
    )


def load_package(
    package_dir: Path,
    aea_project_path: Optional[Path] = None,
    packages_dir: Optional[Path] = None,
    skip_consistency_check: bool = False,
) -> None:
    """Load packages into memory."""
    enforce(
        (aea_project_path is None) != (packages_dir is None),
        "one of either aea_project_path or packages_dir must be specified",
    )
    root_packages = aea_project_path if aea_project_path else packages_dir

    package_path_finder = (
        find_component_directory_from_component_id
        if aea_project_path
        else find_component_directory_from_component_id_in_registry
    )
    if root_packages is None:
        raise ValueError("Packages dir not set!")
    # check the path points to a valid AEA package
    package_type = determine_package_type_for_directory(package_dir)
    if package_type != PackageType.AGENT:
        component_type = ComponentType(package_type.value)
        configuration = load_component_configuration(
            component_type, package_dir, skip_consistency_check=skip_consistency_check
        )
        configuration.directory = package_dir
        load_aea_packages_recursively(configuration, package_path_finder, root_packages)

        test_package_dir = package_dir / AEA_TEST_DIRNAME
        enforce(
            test_package_dir.exists(),
            f"tests directory in {package_dir} not found",
            click.ClickException,
        )

    else:
        if aea_project_path:
            # for agent's workdir
            agent_config = AEABuilder.try_to_load_agent_configuration_file(
                cast(Path, aea_project_path)
            )
            load_aea_packages_recursively(
                agent_config, package_path_finder, root_packages
            )
        else:
            # for agents package in packages
            package_configuration = load_package_configuration(
                package_type=package_type,
                directory=package_dir,
                skip_aea_validation=skip_consistency_check,
            )
            package_configuration.directory = package_dir

            # loads dependencies packages
            load_aea_packages_recursively(
                package_configuration, package_path_finder, root_packages
            )

            # requires to populate sys.modules with packages/author/agents
            perform_load_aea_package(
                package_dir,
                package_configuration.author,
                package_type.to_plural(),
                package_configuration.name,
            )

            test_package_dir = package_dir / AEA_TEST_DIRNAME
            enforce(
                test_package_dir.exists(),
                f"tests directory in {package_dir} not found",
                click.ClickException,
            )


def test_package_by_path(
    package_dir: Path,
    pytest_arguments: Sequence[str],
    aea_project_path: Optional[Path] = None,
    packages_dir: Optional[Path] = None,
    cov: bool = False,
    cov_output: Optional[Path] = None,
    append_coverage: bool = False,
    skip_consistency_check: bool = False,
) -> None:
    """
    Test package placed in package_dir.

    :param package_dir: directory of the package
    :param pytest_arguments: arguments to forward to Pytest
    :param aea_project_path: directory to the AEA project
    :param packages_dir: directory of the packages to import from
    :param cov: coverage capture indicator
    :param cov_output: Path to coverage output directory
    :param append_coverage: Append test coverage instead of starting clean
    :param skip_consistency_check: skip the package consistency check
    """
    cov_output = Path(cov_output or Path.cwd()).resolve()

    load_package(
        package_dir,
        aea_project_path,
        packages_dir,
        skip_consistency_check=skip_consistency_check,
    )
    with CoverageContext(
        root_dir=cov_output, append=append_coverage
    ) as coverage_context:
        runtime_args = [
            *get_pytest_args(
                package_dir=package_dir,
                cov=cov,
                coverage_context=coverage_context,
            ),
            *pytest_arguments,
            "-vvvvvvvvvvvvvvv",
        ]
        exit_code = pytest.main(runtime_args)
        if cov:
            coverage_context.generate()

    sys.exit(exit_code)


def test_package_collection(
    available_packages: List[Tuple[str, Path]],
    packages_dir: Path,
    pytest_args: List[str],
    cov: bool,
    coverage_context: CoverageContext,
    authors: Tuple[str, ...],
) -> List[Tuple[int, str]]:
    """Test a collection of packages."""

    failures = []

    for package_type, package_dir in available_packages:
        if authors != () and not any(
            [author in str(package_dir) for author in authors]
        ):
            continue
        test_dir = package_dir / AEA_TEST_DIRNAME
        if not test_dir.exists():
            continue

        load_package(
            package_dir, packages_dir=packages_dir, skip_consistency_check=True
        )
        click.echo(f"Running tests for {package_dir.name} of type {package_type}")
        exit_code = pytest.main(
            [
                *get_pytest_args(
                    package_dir=package_dir, cov=cov, coverage_context=coverage_context
                ),
                *pytest_args,
            ]
        )

        if exit_code:
            if exit_code == pytest.ExitCode.NO_TESTS_COLLECTED:
                click.echo(
                    f"Could not collect tests for for {package_dir.name} of type {package_type}"
                )
                continue

            click.echo(
                f"Running tests for for {package_dir.name} of type {package_type} failed"
            )
            failures.append((exit_code, os.path.sep.join(package_dir.parts[-3:])))

    return failures


def load_aea_packages_recursively(
    config: Union[ComponentConfiguration, AgentConfig, PackageConfiguration],
    package_path_finder: Callable[[Path, ComponentId], Path],
    root_packages: Path,
    already_loaded: Optional[Set[ComponentId]] = None,
) -> None:
    """
    Load all AEA packages recursively.

    It works like 'load_aea_package', but recursively imports all dependencies.

    :param config: the component configuration
    :param package_path_finder: a function that find packages from the packages dir
    :param root_packages: the path to the root of packages dir
    :param already_loaded: the already loaded component ids
    """
    already_loaded = already_loaded if already_loaded else set()
    for dependency_id in config.package_dependencies:
        # TODO: load packages in topological order? Should not matter as at the moment we are not  # pylint: disable=fixme
        #       actually running the modules, just populating sys.modules
        dependency_path = package_path_finder(root_packages, dependency_id)
        dependency_configuration = load_component_configuration(
            dependency_id.component_type, dependency_path
        )
        dependency_configuration.directory = dependency_path
        load_aea_packages_recursively(
            dependency_configuration, package_path_finder, root_packages, already_loaded
        )
    if isinstance(config, ComponentConfiguration):
        # works for component, not for agent config or package config used for agent
        load_aea_package(config)
        already_loaded.add(config.component_id)


def find_component_directory_from_component_id_in_registry(
    registry_path: Path, component_id: ComponentId
) -> Path:
    """Find a component directory from component id in a registry."""
    package_path = (
        registry_path
        / component_id.author
        / component_id.component_type.to_plural()
        / component_id.public_id.name
    )
    if package_path.exists() and package_path.is_dir():
        return package_path

    raise ValueError("Package {} not found.".format(component_id))


def get_pytest_args(
    package_dir: Path,
    cov: bool = False,
    coverage_context: Optional[CoverageContext] = None,
) -> List:
    """Get pytest args for coverage checks."""
    args = [
        str(package_dir / AEA_TEST_DIRNAME),
    ]

    if cov:
        args.extend(
            cast(CoverageContext, coverage_context).pytest_args(test_path=package_dir)
        )

    return args
