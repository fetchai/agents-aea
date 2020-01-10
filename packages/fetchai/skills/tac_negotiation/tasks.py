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

"""This package contains a scaffold of a task."""

from typing import cast

from aea.skills.base import Task
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


class TransactionCleanUpTask(Task):
    """This class implements the cleanup of the transactions class."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def execute(self) -> None:
        """
        Implement the task execution.

        :return: None
        """
        transactions = cast(Transactions, self.context.transactions)
        transactions.cleanup_pending_transactions()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
