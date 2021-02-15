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

"""This CLI tool takes the main dependencies of the Pipfile.lock and prints it to stdout in requirements.txt format."""
import argparse
import json


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser("parse_main_dependencies_from_lock")
    parser.add_argument(
        "pipfile_lock_path", type=argparse.FileType("r"), help="Path to Pipfile.lock."
    )
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), default=None)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()

    pipfile_lock_content = json.load(arguments.pipfile_lock_path)
    requirements = sorted(
        map(
            lambda x: x[0] + x[1]["version"],
            pipfile_lock_content.get("default").items(),
        )
    )

    requirements_content = "\n".join(requirements)
    if arguments.output is None:
        print(requirements_content)
    else:
        arguments.output.write(requirements_content)
