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
from typing import cast

from aea.cli import cli
from aea.protocols.oef.models import Description, Query, Constraint, ConstraintType
from aea.skills.base import SharedClass
from tests.common.click_testing import CliRunner

DEFAULT_COUNTRY = 'UK'
SEARCH_TERM = 'country'
DEFAULT_SEARCH_INTERVAL = 5.0
DEFAULT_MAX_PRICE = 4000
DEFAULT_MAX_DETECTION_AGE = 60 * 60   # 1 hour
DEFAULT_NO_FINDSEARCH_INTERVAL = 5

CLI_LOG_OPTION = ["-v", "OFF"]


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._country = kwargs.pop('country') if 'country' in kwargs.keys() else DEFAULT_COUNTRY
        self._search_interval = cast(float, kwargs.pop('search_interval')) if 'search_interval' in kwargs.keys() else DEFAULT_SEARCH_INTERVAL
        self._no_find_search_interval = cast(float, kwargs.pop('no_find_search_interval')) if 'no_find_search_interval' in kwargs.keys() else DEFAULT_NO_FINDSEARCH_INTERVAL
        self._max_price = kwargs.pop('max_price') if 'max_price' in kwargs.keys() else DEFAULT_MAX_PRICE
        self._max_detection_age = kwargs.pop('max_detection_age') if 'max_detection_age' in kwargs.keys() else DEFAULT_MAX_DETECTION_AGE

        self.runner = CliRunner()

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.carpark_client.shared_classes.strategy.args.country",
                                 DEFAULT_COUNTRY], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.carpark_client.shared_classes.strategy.args.search_interval",
                                 DEFAULT_SEARCH_INTERVAL], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.carpark_client.shared_classes.strategy.args.no_find_search_interval",
                                 DEFAULT_NO_FINDSEARCH_INTERVAL], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.carpark_client.shared_classes.strategy.args.max_price",
                                 DEFAULT_MAX_PRICE], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.carpark_client.shared_classes.strategy.args.max_detection_age",
                                 DEFAULT_MAX_DETECTION_AGE], standalone_mode=False)

        super().__init__(**kwargs)

        self.is_searching = True

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query([Constraint('longitude', ConstraintType("!=", 0.0))], model=None)
        return query

    def on_submit_search(self):
        """Call when you submit a search ( to suspend searching)."""
        self.is_searching = False

    def on_search_success(self):
        """Call when search returns succesfully."""
        self.is_searching = True

    def on_search_failed(self):
        """Call when search returns with no matches."""
        self.is_searching = True

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = proposal.values["price"] < self._max_price and \
            proposal.values["last_detection_time"] > int(time.time()) - self._max_detection_age

        return result
