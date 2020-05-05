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

"""The tests module contains the tests of the gym example."""

import os
import subprocess  # nosec
import sys
import time
from pathlib import Path

import pytest

from aea.helpers.base import sigint_crossplatform

from ..conftest import CUR_PATH


def test_gym_ex(pytestconfig):
    """Run the gym ex sequence."""
    if pytestconfig.getoption("ci"):
        pytest.skip("Skipping the test since it doesn't work in CI.")

    # run the example
    try:
        process = subprocess.Popen(  # nosec
            [
                sys.executable,
                str(Path(CUR_PATH, "..", "examples/gym_ex/train.py").resolve()),
                "--nb-steps",
                "50",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(5.0)
    finally:
        sigint_crossplatform(process)
        process.wait(timeout=10)

        if not process.returncode == 0:
            poll = process.poll()
            if poll is None:
                process.terminate()
                process.wait(2)
