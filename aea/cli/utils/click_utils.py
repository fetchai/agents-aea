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

"""Module with click utils of the aea cli."""

import os
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional

import click

from aea.cli.utils.config import handle_dotted_path, try_to_load_agent_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, PublicId
from aea.exceptions import AEAException


class ConnectionsOption(click.Option):
    """Click option for the --connections option in 'aea run'."""

    def type_cast_value(self, ctx, value) -> Optional[List[PublicId]]:
        """
        Parse the list of string passed through command line.

        E.g. from 'stub,local' to ['stub', 'local'].

        :param ctx: the click context
        :param value: the list of connection names, as a string.
        :return:
        """
        if value is None:
            return None
        try:

            def arg_strip(s):
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


class PublicIdParameter(click.ParamType):
    """Define a public id parameter for Click applications."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the Public Id parameter.

        Just forwards arguments to parent constructor.
        """
        super().__init__(*args, **kwargs)  # pylint: disable=useless-super-delegation

    def get_metavar(self, param):
        """Return the metavar default for this param if it provides one."""
        return "PUBLIC_ID"

    def convert(self, value, param, ctx):
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        try:
            return PublicId.from_str(value)
        except ValueError:
            self.fail(value, param, ctx)


class AgentDirectory(click.Path):
    """A click.Path, but with further checks  applications."""

    def __init__(self):
        """Initialize the agent directory parameter."""
        super().__init__(
            exists=True, file_okay=False, dir_okay=True, readable=True, writable=False
        )

    def get_metavar(self, param):
        """Return the metavar default for this param if it provides one."""
        return "AGENT_DIRECTORY"  # pragma: no cover

    def convert(self, value, param, ctx):
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        cwd = os.getcwd()
        path = Path(value)
        try:
            # check that the target folder is an AEA project.
            os.chdir(path)
            fp = open(DEFAULT_AEA_CONFIG_FILE, mode="r", encoding="utf-8")
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


class AEAJsonPathType(click.ParamType):
    """This class implements the JSON-path parameter type for the AEA CLI tool."""

    name = "json-path"

    def convert(self, value, param, ctx):
        """Separate the path between path to resource and json path to attribute.

        Allowed values:
            'agent.an_attribute_name'
            'protocols.my_protocol.an_attribute_name'
            'connections.my_connection.an_attribute_name'
            'contracts.my_contract.an_attribute_name'
            'skills.my_skill.an_attribute_name'
            'vendor.author.[protocols|connections|skills].package_name.attribute_name
        """
        try:
            (
                json_path,
                path_to_resource_configuration,
                config_loader,
            ) = handle_dotted_path(value)
        except AEAException as e:
            self.fail(str(e))
        else:
            ctx.obj.set_config(
                "configuration_file_path", path_to_resource_configuration
            )
            ctx.obj.set_config("configuration_loader", config_loader)
            return json_path
