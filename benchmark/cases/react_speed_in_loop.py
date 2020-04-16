#!/usr/bin/ev python3
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

"""Example performance test using benchmark framework. Test react speed on amount of incoming messages using normal agent operating."""
import time

from benchmark.cases.helpers.dummy_handler import DummyHandler
from benchmark.framework.agency import Agency
from benchmark.framework.cli import TestCli


DUMMMY_AGENT_CONF = {
    "name": "dummy_a",
    "skills": [{"handlers": {"dummy_handler": DummyHandler}}],
}


def react_speed_in_loop(control, inbox_amount=1000):
    """Test inbox message processing in a loop."""
    agency = Agency(**DUMMMY_AGENT_CONF)
    for _ in range(inbox_amount):
        agency.put_inbox(agency.dummy_envelope())

    agency.set_loop_timeout(0.0)
    control.put("Go!")
    with agency:
        while not agency.is_inbox_empty():
            time.sleep(0.1)


if __name__ == "__main__":
    TestCli(react_speed_in_loop).run()
