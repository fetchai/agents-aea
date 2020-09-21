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

"""This package contains a class representing the game."""

from packages.fetchai.skills.tac_control.game import AgentState as BaseAgentState
from packages.fetchai.skills.tac_control.game import Configuration as BaseConfiguration
from packages.fetchai.skills.tac_control.game import Game as BaseGame
from packages.fetchai.skills.tac_control.game import (
    Initialization as BaseInitialization,
)
from packages.fetchai.skills.tac_control.game import Phase as BasePhase
from packages.fetchai.skills.tac_control.game import Registration as BaseRegistration
from packages.fetchai.skills.tac_control.game import Transaction as BaseTransaction
from packages.fetchai.skills.tac_control.game import Transactions as BaseTransactions


AgentState = BaseAgentState


Configuration = BaseConfiguration


Game = BaseGame


Initialization = BaseInitialization


Phase = BasePhase


Registration = BaseRegistration


Transaction = BaseTransaction


Transactions = BaseTransactions
