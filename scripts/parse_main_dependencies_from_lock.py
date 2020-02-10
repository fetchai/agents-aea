#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This CLI tool takes the main dependencies of the Pipfile.lock
and prints it to stdout in requirements.txt format.
"""
import json


def parse_args():
    """Parse CLI arguments."""
    import argparse
    parser = argparse.ArgumentParser("parse_main_dependencies_from_lock")
    parser.add_argument("pipfile_lock_path", type=argparse.FileType("r"),
                        help="Path to Pipfile.lock.")
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), default=None)
    return parser.parse_args()


if __name__ == '__main__':
    arguments = parse_args()

    pipfile_lock_content = json.load(arguments.pipfile_lock_path)
    requirements = sorted(map(lambda x: x[0] + x[1]["version"],
                              pipfile_lock_content.get("default").items()))

    requirements_content = "\n".join(requirements)
    if arguments.output is None:
        print(requirements_content)
    else:
        arguments.output.write(requirements_content)
