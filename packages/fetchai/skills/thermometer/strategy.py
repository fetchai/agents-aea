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

"""This module contains the strategy class."""

import time
from typing import Dict

from temper import Temper

from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


MAX_RETRIES = 10


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def collect_from_data_source(self) -> Dict[str, str]:
        """
        Build the data payload.

        :return: the data
        """
        temper = Temper()
        retries = 0
        degrees = {}
        while retries < MAX_RETRIES:
            results = temper.read()
            if "internal temperature" in results[0].keys():
                degrees = {"thermometer_data": str(results[0]["internal temperature"])}
                break
            self.context.logger.debug("Couldn't read the sensor I am re-trying.")
            time.sleep(0.5)
            retries += 1
        return degrees
