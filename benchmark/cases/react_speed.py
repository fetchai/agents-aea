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


"""Example performance test using benchmark framework. test react speed on amount of incoming messages."""
from benchmark.cases.helpers.dummy_handler import DummyHandler
from benchmark.framework.agency import Agency
from benchmark.framework.cli import TestCli


DUMMMY_AGENT_CONF = {
    "name": "dummy_a",
    "skills": [{"handlers": {"dummy_handler": DummyHandler}}],
}


def react_speed(control, amount=1000):
    """Test react only. Does not run full agent's loop."""
    agency = Agency(**DUMMMY_AGENT_CONF)
    agency.setup()
    for _ in range(amount):
        agency.put_inbox(agency.dummy_envelope())

    control.put("Go!")
    while not agency.is_inbox_empty():
        agency.react()
    agency.close()


if __name__ == "__main__":
    TestCli(react_speed).run()
