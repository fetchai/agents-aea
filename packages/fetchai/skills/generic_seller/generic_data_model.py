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
import sys
from typing import Any, Dict

from aea.helpers.search.models import Attribute, DataModel

SUPPORTED_TYPES = {"str": str, "int": int, "float": float, "bool": bool}

logger = logging.getLogger(__name__)


class Generic_Data_Model(DataModel):
    """Data model for the generic seller aea."""

    def __init__(self, data_model_dict: Dict[str, Any]):
        """Initialise the dataModel."""
        self.attributes = []
        try:
            for _k, v in data_model_dict.items():
                self.attributes.append(
                    Attribute(
                        name=v["name"],
                        type=SUPPORTED_TYPES[v["type"]],
                        is_required=v["is_required"],
                    )
                )
        except Exception:
            logger.error(
                msg="There was an error and could not generate the data model. Check your skill.yaml file."
            )
            sys.exit()

        super().__init__("weather_station_datamodel", self.attributes)
