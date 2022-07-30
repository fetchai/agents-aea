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
"""Useful git tools."""

import shutil
import subprocess  # nosec


def check_working_tree_is_dirty() -> bool:
    """
    Check if the current Git working tree is dirty.

    :return: True if the working tree is not dirty, False otherwise
    """
    print("Checking whether the Git working tree is dirty...")
    result = subprocess.check_output(  # nosec
        [str(shutil.which("git")), "diff", "--stat"]
    )  # nosec
    if len(result) > 0:
        print("Git working tree is dirty:")
        print(result.decode("utf-8"))
        return False
    print("All good!")
    return True
