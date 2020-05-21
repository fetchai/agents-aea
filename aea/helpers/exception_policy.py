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
"""This module contains enum of aea exception policies."""

from enum import Enum


class ExceptionPolicyEnum(Enum):
    """AEA Exception policies."""

    propagate = "propagate"  # just bubble up exception raised. run loop interrupted.
    just_log = (
        "just_log"  # write details in log file, skip exception. continue running.
    )
    stop_and_exit = "stop_and_exit"  # log exception and stop agent with raising AEAException to show it was terminated
