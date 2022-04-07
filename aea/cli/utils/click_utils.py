# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""Module with click utils of the aea cli."""

import os
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

import click
from click import Context, Option, UsageError, argument, option

from aea.cli.registry.settings import (
    REGISTRY_CONFIG_KEY,
    REGISTRY_HTTP,
    REGISTRY_IPFS,
    REGISTRY_LOCAL,
)
from aea.cli.utils.config import get_or_create_cli_config, try_to_load_agent_config
from aea.cli.utils.constants import DUMMY_PACKAGE_ID
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)
from aea.configurations.data_types import PublicId
from aea.helpers.io import open_file


class ConnectionsOption(click.Option):
    """Click option for the --connections option in 'aea run'."""

    def type_cast_value(
        self, ctx: click.Context, value: str
    ) -> Optional[List[PublicId]]:
        """
        Parse the list of string passed through command line.

        E.g. from 'stub,local' to ['stub', 'local'].

        :param ctx: the click context
        :param value: the list of connection names, as a string.
        :return: list of public ids
        """
        if value is None:
            return None
        try:

            def arg_strip(s: str) -> str:
                return s.strip(" '\"")

            input_connection_ids = [
                arg_strip(s) for s in value.split(",") if arg_strip(s) != ""
            ]

            # remove duplicates, while preserving the order
            result = OrderedDict()  # type: OrderedDict[PublicId, None]
            for connection_id_string in input_connection_ids:
                connection_public_id = PublicId.from_str(connection_id_string)
                result[connection_public_id] = None
            return list(result.keys())
        except Exception:  # pragma: no cover
            raise click.BadParameter(value)


class PublicIdOrPathParameter(click.ParamType):
    """Define a public id parameter for Click applications."""

    def __init__(  # pylint: disable=useless-super-delegation
        self, *args: Any, **kwargs: Any
    ) -> None:
        """
        Initialize the Public Id parameter.

        Just forwards arguments to parent constructor.

        :param args: positional arguments
        :param kwargs: keyword arguments
        """
        super().__init__(*args, **kwargs)  # type: ignore

    def get_metavar(self, param: Any) -> str:
        """Return the metavar default for this param if it provides one."""
        return "PUBLIC_ID_OR_PATH"

    @staticmethod
    def _parse_public_id(value: str) -> Optional[PublicId]:
        """Parse public id from string."""

        try:
            return PublicId.from_str(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_path(value: str) -> Optional[Path]:
        """Parse path from string."""
        path = Path(value).absolute()
        if path.is_dir():
            return path
        return None

    def convert(
        self, value: str, param: Any, ctx: Optional[click.Context]
    ) -> Union[PublicId, Path]:
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        parsed_value: Optional[Union[PublicId, Path]]
        parsed_value = self._parse_public_id(value)
        if parsed_value is not None:
            return parsed_value

        parsed_value = self._parse_path(value)
        if parsed_value is None:
            self.fail(value, param, ctx)

        return parsed_value


class PublicIdParameter(click.ParamType):
    """Define a public id parameter for Click applications."""

    def get_metavar(self, param: Any) -> str:
        """Return the metavar default for this param if it provides one."""
        return "PUBLIC_ID_OR_HASH"

    @staticmethod
    def _parse_public_id(value: str) -> Optional[PublicId]:
        """Parse extended public from string."""
        try:
            return PublicId.from_str(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_hash(value: str) -> Optional[PublicId]:
        """Parse extended public from string."""
        try:
            return PublicId.from_json({**DUMMY_PACKAGE_ID.json, "package_hash": value})
        except ValueError:
            return None

    def convert(self, value: str, param: Any, ctx: Optional[click.Context]) -> PublicId:
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""

        parsed = self._parse_public_id(value)
        if parsed is not None:
            return parsed

        parsed = self._parse_hash(value)
        if parsed is None:
            self.fail(value, param, ctx)

        return parsed


class AgentDirectory(click.Path):
    """A click.Path, but with further checks  applications."""

    def __init__(self) -> None:
        """Initialize the agent directory parameter."""
        super().__init__(
            exists=True, file_okay=False, dir_okay=True, readable=True, writable=False
        )

    def get_metavar(self, param: Any) -> str:
        """Return the metavar default for this param if it provides one."""
        return "AGENT_DIRECTORY"  # pragma: no cover

    def convert(self, value: str, param: Any, ctx: click.Context) -> str:  # type: ignore
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        cwd = os.getcwd()
        path = Path(value)
        try:
            # check that the target folder is an AEA project.
            os.chdir(path)
            with open_file(DEFAULT_AEA_CONFIG_FILE, mode="r", encoding="utf-8") as fp:
                ctx.obj.agent_config = ctx.obj.agent_loader.load(fp)
            try_to_load_agent_config(ctx.obj)
            # everything ok - return the parameter to the command
            return value
        except Exception:
            raise click.ClickException(
                "The name provided is not a path to an AEA project."
            )
        finally:
            os.chdir(cwd)


def registry_flag(
    help_local: str = "Use only local registry.",
    help_remote: str = "Use ony remote registry.",
) -> Callable:
    """Choice of one flag between: '--local/--remote'."""

    def wrapper(f: Callable) -> Callable:
        f = option(
            "--local",
            is_flag=True,
            cls=MutuallyExclusiveOption,
            help=help_local,
            mutually_exclusive=["remote",],  # noqa: E231
        )(f)
        f = option(
            "--remote",
            is_flag=True,
            cls=MutuallyExclusiveOption,
            help=help_remote,
            mutually_exclusive=["local",],  # noqa: E231
        )(f)
        return f

    return wrapper


def registry_path_option(f: Callable) -> Callable:
    """Add registry path aea option."""
    return option(
        "--registry-path",
        type=click.Path(dir_okay=True, exists=True, file_okay=False),
        required=False,
        help="Provide a local registry directory full path.",
    )(f)


def registry_flag_(mark_default: bool = True) -> Callable:
    """Choice of one flag between: '--local/--remote'."""

    cli_config = get_or_create_cli_config()
    default_registry = cast(
        str, cli_config.get(REGISTRY_CONFIG_KEY, {}).get("default", REGISTRY_LOCAL)
    )

    def wrapper(f: Callable) -> Callable:
        f = option(
            "--local",
            "registry",
            flag_value=REGISTRY_LOCAL,
            help="For pushing items to local folder.",
            default=(REGISTRY_LOCAL == default_registry) and mark_default,
        )(f)
        f = option(
            "--ipfs",
            "registry",
            flag_value=REGISTRY_IPFS,
            help="For pushing items to ipfs node.",
            default=(REGISTRY_IPFS == default_registry) and mark_default,
        )(f)
        f = option(
            "--http",
            "registry",
            flag_value=REGISTRY_HTTP,
            help="For pushing items to http registry.",
            default=(REGISTRY_HTTP == default_registry) and mark_default,
        )(f)
        return f

    return wrapper


def component_flag(wrap_public_id: bool = False,) -> Callable:
    """Wraps a command with component types argument"""

    def wrapper(f: Callable) -> Callable:
        if wrap_public_id:
            f = argument("public_id", type=PublicIdParameter(), required=True)(f)

        f = argument(
            "component_type",
            type=click.Choice((CONNECTION, CONTRACT, PROTOCOL, SKILL)),
            required=True,
        )(f)

        return f

    return wrapper


class MutuallyExclusiveOption(Option):
    """Represent a mutually exclusive option."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the option."""
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help_ = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help_ + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
            )
        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: Context, opts: Dict[str, Any], args: List[Any]
    ) -> Tuple[Any, List[str]]:
        """
        Handle parse result.

        :param ctx: the click context.
        :param opts: the options.
        :param args: the list of arguments (to be forwarded to the parent class).
        :return: tuple of results
        """
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                f"Illegal usage: `{self.name}` is mutually exclusive with "
                f"arguments `{', '.join(self.mutually_exclusive)}`."
            )

        return super().handle_parse_result(ctx, opts, args)


def password_option(confirmation_prompt: bool = False, **kwargs) -> Callable:  # type: ignore
    """Decorator to ask for input if -p flag was provided or use --password to set password value in command line."""

    def callback(ctx, _, value: bool) -> bool:  # type: ignore
        if value is True:
            ctx.params["password"] = ctx.params.get("password") or click.prompt(
                "Enter password",
                hide_input=True,
                confirmation_prompt=confirmation_prompt,
            )
        return value

    def wrap(fn):  # type: ignore
        return click.option(
            "-p",
            is_flag=True,
            type=bool,
            callback=callback,
            expose_value=False,
            help="Ask for password interactively",
        )(
            click.option(
                "--password",
                type=str,
                is_eager=True,
                metavar="PASSWORD",
                help="Set password for key encryption/decryption",
                **kwargs,
            )(fn)
        )  # type: ignore

    return wrap
