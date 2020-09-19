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

"""
This module contains the classes required for dialogue management.

- DefaultDialogue: The dialogue class maintains state of a dialogue of type default and manages it.
- DefaultDialogues: The dialogues class keeps track of all dialogues of type default.
- OefSearchDialogue: The dialogue class maintains state of a dialogue of type oef_search and manages it.
- OefSearchDialogues: The dialogues class keeps track of all dialogues of type oef_search.
- TacDialogue: The dialogue class maintains state of a dialogue of type tac and manages it.
- TacDialogues: The dialogues class keeps track of all dialogues of type tac.
"""

from packages.fetchai.skills.tac_control.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.skills.tac_control.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.skills.tac_control.dialogues import (
    OefSearchDialogue as BaseOefSearchDialogue,
)
from packages.fetchai.skills.tac_control.dialogues import (
    OefSearchDialogues as BaseOefSearchDialogues,
)
from packages.fetchai.skills.tac_control.dialogues import TacDialogue as BaseTacDialogue
from packages.fetchai.skills.tac_control.dialogues import (
    TacDialogues as BaseTacDialogues,
)


DefaultDialogue = BaseDefaultDialogue

DefaultDialogues = BaseDefaultDialogues

OefSearchDialogue = BaseOefSearchDialogue

OefSearchDialogues = BaseOefSearchDialogues

TacDialogue = BaseTacDialogue

TacDialogues = BaseTacDialogues
