# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Module with decorators of the aea cli."""

import os
import shutil
from functools import update_wrapper
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Union, cast

import click
from jsonschema import ValidationError

from aea.cli.utils.config import try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.configurations.base import (
    PackageType,
    PublicId,
    _check_aea_version,
    _compare_fingerprints,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import VENDOR
from aea.configurations.loader import ConfigLoaders
from aea.exceptions import AEAException, AEAValidationError, enforce
from aea.helpers.base import decorator_with_optional_params
from aea.helpers.io import open_file


pass_ctx = click.make_pass_decorator(Context)


def _validate_config_consistency(ctx: Context, check_aea_version: bool = True) -> None:
    """
    Validate fingerprints for every agent component.

    :param ctx: the context
    :param check_aea_version: whether it should check also the AEA version.
    :raises ValueError: if there is a missing configuration file.
                       or if the configuration file is not valid.
                       or if the fingerprints do not match
    """

    if check_aea_version:
        _check_aea_version(ctx.agent_config)

    packages_public_ids_to_types = dict(
        [
            *map(lambda x: (x, PackageType.PROTOCOL), ctx.agent_config.protocols),
            *map(lambda x: (x, PackageType.CONNECTION), ctx.agent_config.connections,),
            *map(lambda x: (x, PackageType.SKILL), ctx.agent_config.skills),
            *map(lambda x: (x, PackageType.CONTRACT), ctx.agent_config.contracts),
        ]
    )  # type: Dict[PublicId, PackageType]

    for public_id, item_type in packages_public_ids_to_types.items():

        # find the configuration file.
        try:
            # either in vendor/ or in personal packages.
            # we give precedence to custom agent components (i.e. not vendorized).
            package_directory = Path(item_type.to_plural(), public_id.name)
            is_vendor = False
            if not package_directory.exists():
                package_directory = Path(
                    VENDOR, public_id.author, item_type.to_plural(), public_id.name
                )
                is_vendor = True
            # we fail if none of the two alternative works.
            enforce(package_directory.exists(), "Package directory does not exist!")

            loader = ConfigLoaders.from_package_type(item_type)
            config_file_name = _get_default_configuration_file_name_from_type(item_type)
            configuration_file_path = package_directory / config_file_name
            enforce(
                configuration_file_path.exists(),
                "Configuration file path does not exist!",
            )
        except Exception:
            raise ValueError("Cannot find {}: '{}'".format(item_type.value, public_id))

        # load the configuration file.
        try:
            with open_file(configuration_file_path, "r") as fp:
                package_configuration = loader.load(fp)
        except (AEAValidationError, ValidationError) as e:
            raise ValueError(
                "{} configuration file '{}' not valid: {}".format(
                    item_type.value.capitalize(), configuration_file_path, str(e)
                )
            )

        if check_aea_version:
            _check_aea_version(package_configuration)
        _compare_fingerprints(
            package_configuration, package_directory, is_vendor, item_type
        )


def _check_aea_project(
    args: Tuple[Any, ...],
    check_aea_version: bool = True,
    check_finger_prints: bool = False,
) -> None:
    try:
        click_context = args[0]
        ctx = cast(Context, click_context.obj)
        try_to_load_agent_config(ctx)
        skip_consistency_check = ctx.config["skip_consistency_check"]
        if not skip_consistency_check:
            _validate_config_consistency(ctx, check_aea_version=check_aea_version)
        if check_finger_prints:
            _compare_fingerprints(
                ctx.agent_config,
                Path(ctx.cwd),
                is_vendor=False,
                item_type=PackageType.AGENT,
                is_recursive=False,
            )
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@decorator_with_optional_params
def check_aea_project(
    f: Callable, check_aea_version: bool = True, check_finger_prints: bool = False
) -> Callable:
    """
    Check the consistency of the project as a decorator.

    - try to load agent configuration file
    - iterate over all the agent packages and check for consistency.

    :param f: callable
    :param check_aea_version: whether or not to check aea version
    :param check_finger_prints: whether or not to check fingerprints
    :return: callable
    """

    def wrapper(*args: Any, **kwargs: Any) -> Callable:
        _check_aea_project(
            args,
            check_aea_version=check_aea_version,
            check_finger_prints=check_finger_prints,
        )
        return f(*args, **kwargs)

    return update_wrapper(wrapper, f)


def _rmdirs(*paths: str) -> None:
    """
    Remove directories.

    :param paths: paths to folders to remove.
    """
    for path in paths:
        if os.path.exists(path):
            shutil.rmtree(path)


def _cast_ctx(context: Union[Context, click.core.Context]) -> Context:
    """
    Cast a Context object from context if needed.

    :param context: Context or click.core.Context object.

    :return: context object.
    :raises: AEAException if context is none of Context and click.core.Context types.
    """
    if isinstance(context, Context):
        return context
    if isinstance(context, click.core.Context):  # pragma: no cover
        return cast(Context, context.obj)
    raise AEAException(  # pragma: no cover
        "clean_after decorator should be used only on methods with Context "
        "or click.core.Context object as a first argument."
    )


def clean_after(func: Callable) -> Callable:
    """
    Decorate a function to remove created folders after ClickException raise.

    :param func: a method to decorate.

    :return: decorated method.
    """

    def wrapper(
        context: Union[Context, click.core.Context], *args: Any, **kwargs: Any
    ) -> Callable:
        """
        Call a source method, remove dirs listed in ctx.clean_paths if ClickException is raised.

        :param context: context object.
        :param args: positional arguments.
        :param kwargs: keyword arguments.

        :raises ClickException: if caught re-raises it.  # noqa: DAR402

        :return: source method output.
        """
        ctx = _cast_ctx(context)
        try:
            return func(context, *args, **kwargs)
        except click.ClickException as e:
            _rmdirs(*ctx.clean_paths)
            raise e

    return wrapper
