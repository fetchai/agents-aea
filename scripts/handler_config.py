# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""Config for handler consistency check."""
from pathlib import Path


_ROOT_DIR = Path(__file__).parent.parent.absolute()
_PACKAGES_DIR = _ROOT_DIR / "packages"

SKIP_SKILLS = (
    _PACKAGES_DIR / "fetchai" / "skills" / "task_test_skill",
    _PACKAGES_DIR / "fetchai" / "skills" / "error_test_skill",
)
SKIP_HANDLERS = ()
COMMON_HANDLERS = ()
