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

"""This package contains the dataModel for the generic seller aea."""
import logging
from typing import Any, Dict

from aea.helpers.search.models import Attribute, DataModel

SUPPORTED_TYPES = {"str": str, "int": int, "float": float, "bool": bool}

logger = logging.getLogger(__name__)


class Generic_Data_Model(DataModel):
    """Data model for the generic seller aea."""

    def __init__(self, data_model_attributes: Dict[str, Any]):
        """Initialise the dataModel."""
        self.attributes = []
        for values in data_model_attributes.values():
            assert values['type'] in SUPPORTED_TYPES.keys(), "Type is not supported. Use str, int, float or bool"
            assert isinstance(
                SUPPORTED_TYPES[values["type"]], values["name"]
            ), "The datamodel values are of wrong type!"
            assert isinstance(
                bool, values["is_required"]
            ), "Wrong type!! is_required must be bool"
            self.attributes.append(
                Attribute(
                    name=values["name"],
                    type=SUPPORTED_TYPES[values["type"]],
                    is_required=values["is_required"],
                )
            )

        super().__init__("weather_station_datamodel", self.attributes)
