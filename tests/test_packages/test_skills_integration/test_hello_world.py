# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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

"""This test module contains the integration test for the hello_world skill."""
from aea.test_tools.test_cases import AEATestCaseEmpty


class TestHelloWorldSkill(AEATestCaseEmpty):
    """Test that hello_world skill works."""

    capture_log = True

    def test_hello_world(self):
        """Run the hello_world skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("skill", "fetchai/hello_world:0.1.0")

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        check_strings = ("Hello World!",)
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)
