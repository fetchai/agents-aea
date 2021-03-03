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
"""Module with helpers constants."""
from typing import Dict, List, Union


FALSE_EQUIVALENTS = ["f", "false", "False", "0"]
FROM_STRING_TO_TYPE = dict(
    str=str, int=int, bool=bool, float=float, dict=dict, list=list, none=None,
)
JSON_TYPES = Union[Dict, str, List, None, int, float]

NETWORK_REQUEST_DEFAULT_TIMEOUT = 60.0  # in seconds
