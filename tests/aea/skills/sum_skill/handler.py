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

"""This module contains the handler for the 'echo' skill."""

from aea.mail.base import Envelope
from aea.skills.base import Handler


class SumHandler(Handler):
    """Sum handler."""

    SUPPORTED_PROTOCOL = "default"

    def __init__(self, **kwargs):
        """Initialize the handler."""
        print("SumHandler.__init__: arguments: {}".format(kwargs))
        self.counter = 0
        self.envelope = None

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle envelopes.
        
        :param envelope: the envelope
        :return: None
        """
        self.counter =2
        self.envelope = envelope
        print("SumHandler: envelope={}".format(envelope))

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        print("SumHandler: teardown method called.")
        pass
