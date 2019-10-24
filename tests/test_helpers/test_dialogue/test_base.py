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

"""This module contains the tests for the helper module."""
from typing import Dict

from aea.helpers.dialogue.base import DialogueLabel, Dialogue, Dialogues
from aea.protocols.default.message import DefaultMessage


class TestDialogueBase:
    """Test the dialogue/base.py."""

    @classmethod
    def setup(cls):
        """Initialise the class."""
        cls.dialogue_label = DialogueLabel(dialogue_id=1, dialogue_opponent_pbk="opponent",
                                           dialogue_starter_pbk="starter")
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)
        cls.dialogues = Dialogues()

    def test_dialogue_label(self):
        """Test the dialogue_label."""
        assert self.dialogue_label.dialogue_id == 1
        assert self.dialogue_label.dialogue_opponent_pbk == "opponent"
        assert self.dialogue_label.dialogue_starter_pbk == "starter"

        dialogue_label2 = DialogueLabel(dialogue_id=1, dialogue_opponent_pbk="opponent",
                                        dialogue_starter_pbk="starter")

        assert dialogue_label2 == self.dialogue_label

        dialogue_label3 = "This is a test"

        assert not dialogue_label3 == self.dialogue_label

        assert hash(self.dialogue_label) == hash(self.dialogue.dialogue_label)

    def test_dialogue(self):
        """Test the dialogue."""
        assert self.dialogue.is_self_initiated
        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, message=b'Hello')
        self.dialogue.outgoing_extend(message=msg)
        assert "my_message" in self.dialogue._outgoing_messages
        self.dialogue.incoming_extend(message=msg)
        assert "my_message" in self.dialogue._incoming_messages

    def test_dialogues(self):
        """Test the dialogues."""
        assert isinstance(self.dialogues.dialogues, Dict)
        id = self.dialogues._next_dialogue_id()
        assert id > 0
        result = self.dialogues.create_self_initiated(dialogue_opponent_pbk="opponent", dialogue_starter_pbk="starter")
        assert isinstance(result, Dialogue)
        result = self.dialogues.create_opponent_initiated(dialogue_opponent_pbk="opponent", dialogue_id=0)
        assert isinstance(result, Dialogue)

        result = self.dialogues._create(self.dialogue_label)
        assert isinstance(result, Dialogue)
