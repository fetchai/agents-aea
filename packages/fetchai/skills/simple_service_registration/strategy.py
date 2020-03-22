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

"""This package contains a scaffold of a model."""

from typing import Any, Dict, Optional

from aea.helpers.search.models import Description
from aea.skills.base import Model

from packages.fetchai.skills.simple_service_registration.data_model import (
    GenericDataModel,
)

DEFAULT_DATA_MODEL_NAME = "location"
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": "True"},
    "attribute_two": {"name": "city", "type": "str", "is_required": "True"},
}  # type: Optional[Dict[str, Any]]
DEFAULT_SERVICE_DATA = {"country": "UK", "city": "Cambridge"}


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        super().__init__(**kwargs)
        self._oef_msg_id = 0
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        desc = Description(
            self._service_data,
            data_model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return desc
