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

"""This module contains the behaviours for the 'echo' skill."""

from aea.skills.behaviours import TickerBehaviour


class EchoBehaviour(TickerBehaviour):
    """Echo behaviour."""

    def setup(self) -> None:
        """Set up the behaviour."""
        self.context.logger.info("Echo Behaviour: setup method called.")

    def act(self) -> None:
        """Act according to the behaviour."""
        self.context.logger.info("Echo Behaviour: act method called.")

    def teardown(self) -> None:
        """Teardown the behaviour."""
        self.context.logger.info("Echo Behaviour: teardown method called.")
