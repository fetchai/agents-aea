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

"""This module contains a generic data model."""

from typing import Any, Dict, List

from aea.helpers.search.models import Attribute, DataModel

SUPPORTED_TYPES = {"str": str, "int": int, "float": float, "bool": bool}


class GenericDataModel(DataModel):
    """Generic data model."""

    def __init__(self, data_model_name: str, data_model_attributes: Dict[str, Any]):
        """Initialise the dataModel."""
        self.attributes = []  # type: List[Attribute]
        for values in data_model_attributes.values():
            assert (
                values["type"] in SUPPORTED_TYPES.keys()
            ), "Type is not supported. Use str, int, float or bool"
            assert isinstance(values["name"], str), "Name must be a string!"
            assert isinstance(
                values["is_required"], bool
            ), "Wrong type for is_required. Must be bool!"
            self.attributes.append(
                Attribute(
                    name=values["name"],  # type: ignore
                    type=SUPPORTED_TYPES[values["type"]],
                    is_required=values["is_required"],
                )
            )

        super().__init__(data_model_name, self.attributes)
