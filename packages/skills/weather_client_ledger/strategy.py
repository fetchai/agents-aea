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

from typing import cast

from aea.cli import cli
from aea.protocols.oef.models import Description, Query, Constraint, ConstraintType
from aea.skills.base import SharedClass
from tests.common.click_testing import CliRunner

DEFAULT_COUNTRY = 'UK'
SEARCH_TERM = 'country'
DEFAULT_MAX_ROW_PRICE = 5
DEFAULT_MAX_TX_FEE = 2
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'fetchai'

CLI_LOG_OPTION = ["-v", "OFF"]


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self.runner = CliRunner()

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.weather_client_ledger.shared_classes.strategy.args.country",
                                 DEFAULT_COUNTRY], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.weather_client_ledger.shared_classes.strategy.args.max_row_price",
                                 DEFAULT_MAX_ROW_PRICE], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.weather_client_ledger.shared_classes.strategy.args.max_tx_fee",
                                 DEFAULT_MAX_TX_FEE], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.weather_client_ledger.shared_classes.strategy.args.currency_id",
                                 DEFAULT_CURRENCY_PBK], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.weather_client_ledger.shared_classes.strategy.args.ledger_id",
                                 DEFAULT_LEDGER_ID], standalone_mode=False)

        super().__init__(**kwargs)
        self._search_id = 0
        self.is_searching = True

    def get_next_search_id(self) -> int:
        """
        Get the next search id and set the search time.

        :return: the next search id
        """
        self._search_id += 1
        return self._search_id

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query([Constraint(SEARCH_TERM, ConstraintType("==", DEFAULT_COUNTRY))], model=None)
        return query

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = (proposal.values['price'] - proposal.values['seller_tx_fee'] > 0) and \
            (proposal.values['price'] <= DEFAULT_MAX_ROW_PRICE * proposal.values['rows']) and \
            (proposal.values['currency_id'] == DEFAULT_CURRENCY_PBK) and \
            (proposal.values['ledger_id'] == DEFAULT_LEDGER_ID)
        return result

    def is_affordable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an affordable proposal.

        :return: whether it is affordable
        """
        payable = proposal.values['price'] + DEFAULT_MAX_TX_FEE
        ledger_id = proposal.values['ledger_id']
        address = cast(str, self.context.agent_addresses.get(ledger_id))
        balance = self.context.ledger_apis.token_balance(ledger_id, address)
        return balance >= payable
