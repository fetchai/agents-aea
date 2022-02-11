# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

from aea.exceptions import enforce
from aea.helpers.search.models import Attribute, DataModel, Location


SUPPORTED_TYPES = {"str": str, "int": int, "float": float, "bool": bool}


class GenericDataModel(DataModel):  # pylint: disable=too-few-public-methods
    """Generic data model."""

    def __init__(
        self, data_model_name: str, data_model_attributes: Dict[str, Any]
    ) -> None:
        """Initialise the dataModel."""
        attributes = []  # type: List[Attribute]
        for values in data_model_attributes.values():
            enforce(
                values["type"] in SUPPORTED_TYPES.keys(),
                "Type is not supported. Use str, int, float or bool",
            )
            enforce(isinstance(values["name"], str), "Name must be a string!")
            enforce(
                isinstance(values["is_required"], bool),
                "Wrong type for is_required. Must be bool!",
            )
            attributes.append(
                Attribute(
                    name=values["name"],  # type: ignore
                    type_=SUPPORTED_TYPES[values["type"]],
                    is_required=values["is_required"],
                )
            )

        super().__init__(data_model_name, attributes)


AGENT_LOCATION_MODEL = DataModel(
    "location_agent",
    [Attribute("location", Location, True, "The location where the agent is.")],
    "A data model to describe location of an agent.",
)


AGENT_PERSONALITY_MODEL = DataModel(
    "personality_agent",
    [
        Attribute("piece", str, True, "The personality piece key."),
        Attribute("value", str, True, "The personality piece value."),
    ],
    "A data model to describe the personality of an agent.",
)


AGENT_SET_SERVICE_MODEL = DataModel(
    "set_service_key",
    [
        Attribute("key", str, True, "Service key name."),
        Attribute("value", str, True, "Service key value."),
    ],
    "A data model to set service key.",
)


SIMPLE_SERVICE_MODEL = DataModel(
    "simple_service",
    [Attribute("seller_service", str, True, "Service key name.")],
    "A data model to represent a search for a service.",
)


SIMPLE_DATA_MODEL = DataModel(
    "simple_data",
    [Attribute("dataset_id", str, True, "Data set key name.")],
    "A data model to represent a search for a data set.",
)


AGENT_REMOVE_SERVICE_MODEL = DataModel(
    "remove_service_key",
    [Attribute("key", str, True, "Service key name.")],
    "A data model to remove service key.",
)
