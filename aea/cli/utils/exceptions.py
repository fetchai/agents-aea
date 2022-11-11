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

"""Module with exceptions of the aea cli."""

from warnings import warn

import click

from aea.exceptions import AEAException


def aev_flag_depreaction() -> None:
    """Deprecation warning for `--aev` flag."""
    message = "`--aev` flag is deprecated and will be removed in v2.0.0, usage of envrionment varibales is default now."
    click.echo(message)
    warn(message, DeprecationWarning, stacklevel=2)


class AEAConfigException(AEAException):
    """Exception about AEA configuration."""
