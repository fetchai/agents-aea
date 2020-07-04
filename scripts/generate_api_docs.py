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
    "aea.aea_builder": "api/aea_builder.md",
    "aea.agent": "api/agent.md",
    "aea.agent_loop": "api/agent_loop.md",
    "aea.launcher": "api/launcher.md",
    "aea.multiplexer": "api/multiplexer.md",
    "aea.runner": "api/runner.md",
    "aea.runtime": "api/runtime.md",
    "aea.components.base": "api/components/base.md",
    "aea.components.loader": "api/components/loader.md",
    "aea.configurations.base": "api/configurations/base.md",
    "aea.configurations.constants": "api/configurations/constants.md",
    "aea.configurations.loader": "api/configurations/loader.md",
    "aea.connections.base": "api/connections/base.md",
    "aea.connections.stub.connection": "api/connections/stub/connection.md",
    "aea.context.base": "api/context/base.md",
    "aea.contracts.base": "api/contracts/base.md",
    "aea.contracts.ethereum": "api/contracts/ethereum.md",
    "aea.crypto.base": "api/crypto/base.md",
    "aea.crypto.cosmos": "api/crypto/cosmos.md",
    "aea.crypto.ethereum": "api/crypto/ethereum.md",
    "aea.crypto.fetchai": "api/crypto/fetchai.md",
    "aea.crypto.helpers": "api/crypto/helpers.md",
    "aea.crypto.ledger_apis": "api/crypto/ledger_apis.md",
    "aea.crypto.wallet": "api/crypto/wallet.md",
    "aea.crypto.registries.base": "api/crypto/registries/base.md",
    "aea.decision_maker.base": "api/decision_maker/base.md",
    "aea.decision_maker.default": "api/decision_maker/default.md",
    "aea.helpers.dialogue.base": "api/helpers/dialogue/base.md",
    "aea.helpers.ipfs.base": "api/helpers/ipfs/base.md",
    "aea.helpers.preference_representations.base": "api/helpers/preference_representations/base.md",
    "aea.helpers.search.generic": "api/helpers/search/generic.md",
    "aea.helpers.search.models": "api/helpers/search/models.md",
    "aea.helpers.transaction.base": "api/helpers/transaction/base.md",
    "aea.helpers.async_friendly_queue": "api/helpers/async_friendly_queue.md",
    "aea.helpers.async_utils": "api/helpers/async_utils.md",
    "aea.helpers.base": "api/helpers/base.md",
    "aea.helpers.exception_policy": "api/helpers/exception_policy.md",
    "aea.helpers.exec_timeout": "api/helpers/exec_timeout.md",
    "aea.helpers.multiple_executor": "api/helpers/multiple_executor.md",
    "aea.identity.base": "api/identity/base.md",
    "aea.mail.base": "api/mail/base.md",
    "aea.protocols.base": "api/protocols/base.md",
    "aea.protocols.generator": "api/protocols/generator.md",
    "aea.protocols.default.custom_types": "api/protocols/default/custom_types.md",
    "aea.protocols.default.message": "api/protocols/default/message.md",
    "aea.protocols.default.serialization": "api/protocols/default/serialization.md",
    "aea.protocols.signing.custom_types": "api/protocols/signing/custom_types.md",
    "aea.protocols.signing.message": "api/protocols/signing/message.md",
    "aea.protocols.signing.serialization": "api/protocols/signing/serialization.md",
    "aea.protocols.state_update.message": "api/protocols/state_update/message.md",
    "aea.protocols.state_update.serialization": "api/protocols/state_update/serialization.md",
    "aea.registries.base": "api/registries/base.md",
    "aea.registries.filter": "api/registries/filter.md",
    "aea.registries.resources": "api/registries/resources.md",
    "aea.skills.base": "api/skills/base.md",
    "aea.skills.behaviours": "api/skills/behaviours.md",
    "aea.skills.tasks": "api/skills/tasks.md",
    "aea.skills.error.handlers": "api/skills/error/handlers.md",
    "aea.test_tools.generic": "api/test_tools/generic.md",
    "aea.test_tools.test_cases": "api/helpers/test_cases.md",
}


def create_subdir(path) -> None:
    """
    Create a subdirectory.

    :param path: the directory path
    """
    directory = "/".join(path.split("/")[:-1])
    Path(directory).mkdir(parents=True, exist_ok=True)


def replace_underscores(text: str) -> str:
    """
    Replace escaped underscores in a text.

    :return: the processed text
    """
    text_a = text.replace("\\_\\_", "`__`")
    text_b = text_a.replace("\\_", "`_`")
    return text_b


def save_to_file(path: str, text: str) -> None:
    """
    Save to a file path.

    :param path: the path
    :param text: the text
    :return: None
    """
    with open(path, "w") as f:
        f.write(text)


def generate_api_docs():
    """Generate the api docs."""
    for module, rel_path in MODULES_TO_PATH.items():
        path = DOCS_DIR + rel_path
        create_subdir(path)
        pydoc = subprocess.Popen(  # nosec
            ["pydoc-markdown", "-m", module, "-I", "."], stdout=subprocess.PIPE
        )
        stdout, _ = pydoc.communicate()
        pydoc.wait()
        stdout_text = stdout.decode("utf-8")
        text = replace_underscores(stdout_text)
        save_to_file(path, text)


if __name__ == "__main__":
    res = shutil.which("pydoc-markdown")
    if res is None:
        print("Please install pydoc-markdown first: `pip install pydoc-markdown`")
        sys.exit(1)
    generate_api_docs()
