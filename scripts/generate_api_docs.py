#!/usr/bin/env python3
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
This tool generates the API docs.
"""

import shutil
import subprocess  # nosec
import sys
from pathlib import Path

DOCS_DIR = "docs/"
MODULES_TO_PATH = {
    "aea.aea": "api/aea.md",
    "aea.agent": "api/agent.md",
    "aea.configurations.base": "api/configurations/base.md",
    "aea.configurations.loader": "api/configurations/loader.md",
    "aea.connections.base": "api/connections/base.md",
    "aea.connections.stub.connection": "api/connections/stub/connection.md",
    "aea.context.base": "api/context/base.md",
    "aea.crypto.base": "api/crytpo/base.md",
    "aea.crypto.ethereum": "api/crypto/ethereum.md",
    "aea.crypto.fetchai": "api/crypto/fetchai.md",
    "aea.crypto.ledger_apis": "api/crypto/ledger_apis.md",
    "aea.crypto.wallet": "api/crypto/wallet.md",
    "aea.decision_maker.base": "api/decision_maker/base.md",
    "aea.decision_maker.messages.base": "api/decision_maker/messages/base.md",
    "aea.decision_maker.messages.state_update": "api/decision_maker/messages/state_update.md",
    "aea.decision_maker.messages.transaction": "api/decision_maker/messages/transaction.md",
    "aea.helpers.dialogue.base": "api/helpers/dialogue/base.md",
    "aea.helpers.search.generic": "api/helpers/search/generic.md",
    "aea.helpers.search.models": "api/helpers/search/models.md",
    "aea.identity.base": "api/identity/base.md",
    "aea.mail.base": "api/mail/base.md",
    "aea.protocols.base": "api/protocols/base.md",
    "aea.protocols.default.message": "api/protocols/default/message.md",
    "aea.protocols.default.serialization": "api/protocols/default/serialization.md",
    "aea.registries.resources": "api/registries/resources.md",
    "aea.skills.base": "api/skills/base.md",
    "aea.skills.behaviours": "api/skills/behaviours.md",
    "aea.skills.tasks": "api/skills/tasks.md",
    "aea.skills.error.handlers": "api/skills/error/handlers.md",
}


def create_subdir(path):
    directory = "/".join(path.split("/")[:-1])
    Path(directory).mkdir(parents=True, exist_ok=True)


def replace_underscores(text):
    text_a = text.replace("\\_\\_", "`__`")
    text_b = text_a.replace("\\_", "`_`")
    return text_b


def save_to_file(path, text):
    with open(path, "w") as f:
        f.write(text)


def generate_api_docs():
    for module, rel_path in MODULES_TO_PATH.items():
        path = DOCS_DIR + rel_path
        create_subdir(path)
        pydoc = subprocess.Popen(  # nosec
            ["pydoc-markdown", "-m", module, "-I", "."], stdout=subprocess.PIPE
        )
        stdout, stderr = pydoc.communicate()
        pydoc.wait()
        stdout_text = stdout.decode("utf-8")
        text = replace_underscores(stdout_text)
        save_to_file(path, text)


if __name__ == "__main__":
    res = shutil.which("pydoc-markdown")
    if res is None:
        print(
            "Please install pydoc-markdown first! See the following link: https://github.com/NiklasRosenstein/pydoc-markdown/tree/develop"
        )
        sys.exit(1)
    generate_api_docs()
