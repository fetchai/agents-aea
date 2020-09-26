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

from __future__ import print_function

import argparse
import json
import os
import subprocess  # nosec
import sys


def run(cmd):
    print(" ".join(cmd))
    c = subprocess.Popen(cmd)  # nosec
    try:
        c.wait()
    except KeyboardInterrupt:
        pass
    finally:
        poll = c.poll()
        if poll is None:
            c.terminate()
            c.wait(2)
    return c.returncode


def error(*x):
    print("".join([str(xx) for xx in x]), file=sys.stderr)


def fail(*x):
    error(x)
    exit(1)


def pull_image(run_sudo, img):
    c = []

    if run_sudo:
        c += ["sudo"]
    c += [
        "docker",
        "pull",
        img,
    ]
    r = run(c)
    if r != 0:
        error("can't pull " + img)


def parse_command(j):
    cmd = []
    used_keys = ["positional_args"]
    for key in j["positional_args"]:
        cmd.append(str(j[key]))
        used_keys.append(key)
    for key in j:
        if key in used_keys:
            continue
        cmd.extend(["--" + key, str(j[key])])
    return cmd


def launch_job(args, j):
    img = j["image"]
    if "/" in img:
        pull_image(args.sudo, img)

    c = []
    if args.sudo:
        c += ["sudo"]
    c += ["docker", "run"]
    if args.background:
        c += ["-d"]
    elif not args.disable_stdin:
        c += ["-it"]
    else:
        c += ["-t"]

    if args.name:
        c += ["--name"]
        c += [args.name]

    work_dir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.abspath(os.path.join(work_dir, "..", ".."))
    print("Work dir: ", work_dir)
    c += ["-v", work_dir + ":/config", "-v", project_dir + "/data/oef-logs:/logs"]

    for arg in j["params"]:
        c += map(lambda x: x.replace("$PWD", project_dir), arg)

    c += [img]

    cmd_config = j["cmd"].get(args.cmd, None)
    if not cmd_config:
        fail("Selected command {} not configured in config file!".format(args.cmd))

    c.extend(parse_command(cmd_config))
    extra_args = [a for a in args.rest if a != "--"]
    print("Extra arguments to search: ", extra_args)
    c += extra_args
    r = run(c)
    if r != 0:
        fail("can't launch " + img)


def main(args):
    with open(args.config, "r") as f:
        config = json.load(f)
    launch_job(args, config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", required=True, type=str, help="Publish the image to GCR"
    )
    parser.add_argument(
        "--sudo", required=False, action="store_true", help="Run docker as root"
    )
    parser.add_argument(
        "--background",
        required=False,
        action="store_true",
        help="Run image in background.",
    )
    parser.add_argument(
        "--disable_stdin",
        required=False,
        action="store_true",
        help="Disable disable_stdin.",
    )
    parser.add_argument(
        "-n", "--name", required=False, type=str, help="give thre container a name"
    )
    parser.add_argument(
        "--cmd",
        required=False,
        type=str,
        default="oef-search",
        help="The available commands are defined"
        " in the config file "
        "('cmd' dictionary) ",
    )
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    main(parser.parse_args())
