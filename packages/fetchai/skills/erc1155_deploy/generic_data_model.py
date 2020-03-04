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

"""This package contains the dataModel for the erc1155 deploy skill aea."""
from typing import Any, Dict

from aea.helpers.search.models import Attribute, DataModel

SUPPORTED_TYPES = {"str": str, "int": int, "float": float, "bool": bool}


class Generic_Data_Model(DataModel):
    """Data model for the the erc1155 deploy skill aea."""

    def __init__(self, data_model_attributes: Dict[str, Any]):
        """Initialise the dataModel."""
        self.attributes = []
        for values in data_model_attributes.values():
            assert (
                values["type"] in SUPPORTED_TYPES.keys()
            ), "Type is not supported. Use str, int, float or bool"
            assert isinstance(
                values["name"], (SUPPORTED_TYPES[values["type"]],)
            ), "The datamodel values are of wrong type!"
            assert isinstance(
                values["is_required"], bool
            ), "Wrong type!! is_required must be bool"
            self.attributes.append(
                Attribute(
                    name=values["name"],  # type: ignore
                    type=SUPPORTED_TYPES[values["type"]],
                    is_required=values["is_required"],
                )
            )

        super().__init__("erc1155_deploy_skill", self.attributes)
