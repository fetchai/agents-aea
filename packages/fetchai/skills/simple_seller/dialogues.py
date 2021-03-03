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
This module contains the classes required for dialogue management (reused from generic_seller skill).

- DefaultDialogues: The dialogues class keeps track of all dialogues of type default.
- FipaDialogues: The dialogues class keeps track of all dialogues of type fipa.
- LedgerApiDialogues: The dialogues class keeps track of all dialogues of type ledger_api.
- OefSearchDialogues: The dialogues class keeps track of all dialogues of type oef_search.
"""

from packages.fetchai.skills.generic_seller.dialogues import (
    DefaultDialogues as GenericDefaultDialogues,
)
from packages.fetchai.skills.generic_seller.dialogues import (
    FipaDialogues as GenericFipaDialogues,
)
from packages.fetchai.skills.generic_seller.dialogues import (
    LedgerApiDialogues as GenericLedgerApiDialogues,
)
from packages.fetchai.skills.generic_seller.dialogues import (
    OefSearchDialogues as GenericOefSearchDialogues,
)


DefaultDialogues = GenericDefaultDialogues
FipaDialogues = GenericFipaDialogues
LedgerApiDialogues = GenericLedgerApiDialogues
OefSearchDialogues = GenericOefSearchDialogues
