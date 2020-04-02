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

"""The base contract."""
import json
from pathlib import Path
from typing import Any, Dict, Optional

from aea.configurations.base import ContractConfig, ContractId
from aea.configurations.components import Component


class Contract(Component):
    """Abstract definition of a contract."""

    def __init__(
        self, config: ContractConfig, contract_interface: Dict[str, Any],
    ):
        """
        Initialize the contract.

        :param config: the contract configurations.
        :param contract_interface: the contract interface
        """
        super().__init__(config)
        self._contract_interface = contract_interface  # type: Dict[str, Any]

    @property
    def id(self) -> ContractId:
        """Get the name."""
        return self.public_id

    @property
    def config(self) -> ContractConfig:
        """Get the configuration."""
        # return self._config
        return self._configuration  # type: ignore

    @property
    def contract_interface(self) -> Dict[str, Any]:
        """Get the contract interface."""
        return self._contract_interface
