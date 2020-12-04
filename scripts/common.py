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

"""Common utils for scripts."""
import subprocess  # nosec
import sys


def check_working_tree_is_dirty() -> None:
    """Check if the current Git working tree is dirty."""
    print("Checking whether the Git working tree is dirty...")
    result = subprocess.check_output(["git", "diff", "--stat"])  # nosec
    if len(result) > 0:
        print("Git working tree is dirty:")
        print(result.decode("utf-8"))
        sys.exit(1)
    else:
        print("All good!")
