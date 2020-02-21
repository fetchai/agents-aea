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

"""This package contains the dataModel for the carpark detection agent."""

from aea.helpers.search.models import Attribute, DataModel


class CarParkDataModel(DataModel):
    """Data model for the Carpark Agent."""

    def __init__(self):
        """Initialise the dataModel."""
        self.ATTRIBUTE_LATITUDE = Attribute("latitude", float, True)
        self.ATTRIBUTE_LONGITUDE = Attribute("longitude", float, True)
        self.ATTRIBUTE_UNIQUE_ID = Attribute("unique_id", str, True)

        super().__init__(
            "carpark_detection_datamodel",
            [
                self.ATTRIBUTE_LATITUDE,
                self.ATTRIBUTE_LONGITUDE,
                self.ATTRIBUTE_UNIQUE_ID,
            ],
        )
