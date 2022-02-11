# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the tests for the code-blocks in the skill.md file."""
from pathlib import Path

import mistune

from aea.skills.behaviours import OneShotBehaviour
from aea.skills.tasks import Task

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import compile_and_exec


class TestSkillDocs:
    """Test the integrity of the code-blocks in skill.md"""

    @classmethod
    def setup_class(cls):
        """Test skill.md"""
        markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

        skill_doc_file = Path(ROOT_DIR, "docs", "skill.md")
        doc = markdown_parser(skill_doc_file.read_text())
        # get only code blocks
        cls.code_blocks = list(filter(lambda x: x["type"] == "block_code", doc))

    def test_context(self):
        """Test the code in context."""
        block = self.code_blocks[0]
        expected = "self.context.outbox.put_message(message=reply)"
        assert block["text"].strip() == expected
        assert block["info"].strip() == "python"

    # TODO add tests for new_handlers queue

    def test_hello_world_behaviour(self):
        """Test the code in the 'behaviours.py' section."""
        # here, we test the definition of a custom class
        offset = 2
        block = self.code_blocks[offset]
        text = block["text"]

        # check that the code can be executed
        code_obj = compile(text, "fakemodule", "exec")
        locals_dict = {}
        exec(code_obj, globals(), locals_dict)  # nosec

        # some consistency check on the behaviour class.
        HelloWorldBehaviour = locals_dict["HelloWorldBehaviour"]
        assert issubclass(HelloWorldBehaviour, OneShotBehaviour)

        # here, we test the code example for adding the new custom behaviour to the list
        # of new behaviours
        block = self.code_blocks[offset + 1]
        text = block["text"]
        assert (
            text.strip()
            == 'self.context.new_behaviours.put(HelloWorldBehaviour(name="hello_world", skill_context=self.context))'
        )

        block = self.code_blocks[offset + 2]
        assert (
            block["text"] == "def hello():\n"
            '    print("Hello, World!")\n'
            "\n"
            'self.context.new_behaviours.put(OneShotBehaviour(act=hello, name="hello_world", skill_context=self.context))\n'
        )

    def test_task(self):
        """Test the code blocks of the 'tasks.py' section."""
        # test code of task definition
        offset = 5
        block = self.code_blocks[offset]
        locals_dict = compile_and_exec(block["text"])

        nth_prime_number = locals_dict["nth_prime_number"]
        assert nth_prime_number(1) == 2
        assert nth_prime_number(2) == 3
        assert nth_prime_number(3) == 5
        assert nth_prime_number(4) == 7
        LongTask = locals_dict["LongTask"]
        assert issubclass(LongTask, Task)
        LongTask()
