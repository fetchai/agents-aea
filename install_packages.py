#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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

"""The install packages script"""
import re
import subprocess
import sys
from pathlib import Path
from typing import List

import toml


def _load_groups():
    data = toml.loads(Path("pyproject.toml").read_text())
    return list(data["tool"]["poetry"]["group"].keys())


def _load_dependencies() -> List[str]:
    groups = ",".join(_load_groups())
    text = subprocess.check_output(
        f"poetry export --with {groups}", shell=True, text=True
    )
    text = text.replace("\\\n", " ")
    lines = text.splitlines()
    lines = [i.split(" ")[0] for i in lines]
    return lines


RE = re.compile("(.*)[=><]")

if __name__ == "__main__":
    packages = sys.argv[1:]
    requirements = _load_dependencies()

    to_install = []
    for package in packages:
        for requirement in requirements:
            if re.match(f"^{package}([<>=].*)?$", requirement):
                to_install.append(requirement.strip())
    if not to_install:
        raise ValueError("No packages found to install")
    print("installing", ", ".join(to_install))
    subprocess.check_call([sys.executable, "-m", "pip", "install", *to_install])
