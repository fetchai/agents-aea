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

"""This CLI tool freezes the dependencies."""
import argparse
import re
import subprocess  # nosec


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser("freeze_dependencies")
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), default=None)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()

    pip_freeze_call = subprocess.Popen(  # nosec
        ["pip", "freeze"], stdout=subprocess.PIPE
    )
    (stdout, stderr) = pip_freeze_call.communicate()
    requirements = stdout.decode("utf-8")

    # remove 'aea' itself
    regex = re.compile("^aea(==.*| .*)?$", re.MULTILINE)
    requirements = re.sub(regex, "", requirements)
    if arguments.output is None:
        print(requirements)
    else:
        arguments.output.write(requirements)
