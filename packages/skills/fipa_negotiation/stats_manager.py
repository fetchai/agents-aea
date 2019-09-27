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

"""This module contains a class to handle statistics on the TAC."""

import time
from enum import Enum
from threading import Thread
from typing import Dict, Optional

import numpy as np

from aea.channels.oef.connection import MailStats


class EndState(Enum):
    """This class defines the end states of a dialogue."""

    SUCCESSFUL = 0
    DECLINED_CFP = 1
    DECLINED_PROPOSE = 2
    DECLINED_ACCEPT = 3


class StatsManager(object):
    """Class to handle statistics on the game."""

    def __init__(self, mail_stats, dashboard, task_timeout: float = 2.0) -> None:
        """
        Initialize a StatsManager.

        :param mail_stats: the mail stats of the mail box.
        :param dashboard: The dashboard.
        :param task_timeout: seconds to sleep for the task

        :return: None
        """
        self.dashboard = dashboard
        self._update_stats_task_is_running = False
        self._update_stats_task = None  # type: Optional[Thread]
        self._update_stats_task_timeout = task_timeout

        self._mail_stats = mail_stats

        self._self_initiated_dialogue_stats = {EndState.SUCCESSFUL: 0,
                                               EndState.DECLINED_CFP: 0,
                                               EndState.DECLINED_PROPOSE: 0,
                                               EndState.DECLINED_ACCEPT: 0}  # type: Dict[EndState, int]
        self._other_initiated_dialogue_stats = {EndState.SUCCESSFUL: 0,
                                                EndState.DECLINED_CFP: 0,
                                                EndState.DECLINED_PROPOSE: 0,
                                                EndState.DECLINED_ACCEPT: 0}  # type: Dict[EndState, int]

    @property
    def mail_stats(self) -> MailStats:
        """Get the mail stats."""
        return self._mail_stats

    @property
    def self_initiated_dialogue_stats(self) -> Dict[EndState, int]:
        """Get the stats dictionary on self initiated dialogues."""
        return self._self_initiated_dialogue_stats

    @property
    def other_initiated_dialogue_stats(self) -> Dict[EndState, int]:
        """Get the stats dictionary on other initiated dialogues."""
        return self._other_initiated_dialogue_stats

    def add_dialogue_endstate(self, end_state: EndState, is_self_initiated: bool) -> None:
        """
        Add dialogue endstate stats.

        :param end_state: the end state of the dialogue
        :param is_self_initiated: whether the dialogue is initiated by the agent or the opponent

        :return: None
        """
        if is_self_initiated:
            self._self_initiated_dialogue_stats[end_state] += 1
        else:
            self._other_initiated_dialogue_stats[end_state] += 1

    def avg_search_time(self) -> float:
        """
        Average the search timedeltas.

        :return: avg search time in seconds
        """
        timedeltas = list(self.mail_stats._search_timedelta.values())
        if len(timedeltas) == 0:
            result = 0.0
        else:
            result = sum(timedeltas) / len(timedeltas)
        return result

    def avg_search_result_counts(self) -> float:
        """
        Average the search result counts.

        :return: avg search result counts
        """
        counts = list(self.mail_stats._search_result_counts.values())
        if len(counts) == 0:
            result = 0.0
        else:
            result = sum(counts) / len(counts)
        return result

    def negotiation_metrics_self(self) -> np.ndarray:
        """
        Get the negotiation metrics on self initiated dialogues.

        :return: an array containing the metrics
        """
        return self._negotiation_metrics(self.self_initiated_dialogue_stats)

    def negotiation_metrics_other(self) -> np.ndarray:
        """
        Get the negotiation metrics on other initiated dialogues.

        :return: an array containing the metrics
        """
        return self._negotiation_metrics(self.other_initiated_dialogue_stats)

    def _negotiation_metrics(self, dialogue_stats: Dict[EndState, int]) -> np.ndarray:
        """
        Get the negotiation metrics.

        :param dialogue_stats: the dialogue statistics

        :return: an array containing the metrics
        """
        result = np.zeros((4), dtype=np.int)
        result[0] = dialogue_stats[EndState.SUCCESSFUL]
        result[1] = dialogue_stats[EndState.DECLINED_CFP]
        result[2] = dialogue_stats[EndState.DECLINED_PROPOSE]
        result[3] = dialogue_stats[EndState.DECLINED_ACCEPT]
        return result

    def start(self) -> None:
        """
        Start the stats manager.

        :return: None
        """
        if not self._update_stats_task_is_running:
            self._update_stats_task_is_running = True
            self._update_stats_task = Thread(target=self.update_stats_job)
            self._update_stats_task.start()

    def stop(self) -> None:
        """
        Stop the stats manager.

        :return: None
        """
        assert self._update_stats_task is not None, "Call start before calling stop."
        if self._update_stats_task_is_running:
            self._update_stats_task_is_running = False
            self._update_stats_task.join()

    def update_stats_job(self) -> None:
        """
        Periodically update the dashboard.

        :return: None
        """
        while self._update_stats_task_is_running:
            time.sleep(self._update_stats_task_timeout)
            self.dashboard.update_from_stats_manager(self, append=True)
