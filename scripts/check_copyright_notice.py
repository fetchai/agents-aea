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
This script checks that all the Python files of the repository have:

- (optional) the Python shebang
- the encoding header;
- the copyright notice;

It is assumed the script is run from the repository root.
"""

import itertools
import re
import shutil
import subprocess  # nosec
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


GIT_PATH = shutil.which("git")
SUPPORTED_YEARS_FETCHAI = ["2019", "2020", "2021"]
SUPPORTED_YEARS_VALORY = ["2021", "2022"]


HEADER_REGEX_FETCHAI = re.compile(
    fr"""(#!/usr/bin/env python3
)?# -\*- coding: utf-8 -\*-
# ------------------------------------------------------------------------------
#
#   Copyright ((20\d\d)(-20\d\d)?) Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2\.0 \(the \"License\"\);
#   you may not use this file except in compliance with the License\.
#   You may obtain a copy of the License at
#
#       http://www\.apache\.org/licenses/LICENSE-2\.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an \"AS IS\" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied\.
#   See the License for the specific language governing permissions and
#   limitations under the License\.
#
# ------------------------------------------------------------------------------
""",
    re.MULTILINE,
)

HEADER_REGEX_VALORY = re.compile(
    r"""(#!/usr/bin/env python3
)?# -\*- coding: utf-8 -\*-
# ------------------------------------------------------------------------------
#
#   Copyright ((202\d)(-202\d)?) Valory AG
#
#   Licensed under the Apache License, Version 2\.0 \(the \"License\"\);
#   you may not use this file except in compliance with the License\.
#   You may obtain a copy of the License at
#
#       http://www\.apache\.org/licenses/LICENSE-2\.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an \"AS IS\" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied\.
#   See the License for the specific language governing permissions and
#   limitations under the License\.
#
# ------------------------------------------------------------------------------
""",
    re.MULTILINE,
)

HEADER_REGEX_MIXED = re.compile(
    fr"""(#!/usr/bin/env python3
)?# -\*- coding: utf-8 -\*-
# ------------------------------------------------------------------------------
#
#   Copyright ((202\d)(-202\d)?) Valory AG
#   Copyright ((20\d\d)(-20\d\d)?) Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2\.0 \(the \"License\"\);
#   you may not use this file except in compliance with the License\.
#   You may obtain a copy of the License at
#
#       http://www\.apache\.org/licenses/LICENSE-2\.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an \"AS IS\" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied\.
#   See the License for the specific language governing permissions and
#   limitations under the License\.
#
# ------------------------------------------------------------------------------
""",
    re.MULTILINE,
)

REGEX_LIST: List[Tuple[str, re.Pattern]] = [
    ("FetchAI", HEADER_REGEX_FETCHAI),
    ("Valory", HEADER_REGEX_VALORY),
    ("Mixed", HEADER_REGEX_MIXED),
]


def _check_copyright(file: Path, match: re.Match) -> Tuple[bool, str]:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :param match: match object.
    :return: True if the file is compliant with the checks, False otherwise.
    """

    copyright_years_str = match.groups(0)[1]  # type: ignore
    copyright_years = tuple(int(i) for i in copyright_years_str.split("-"))
    date_string, _ = subprocess.Popen(  # pylint: disable=consider-using-with  # nosec
        [str(GIT_PATH), "log", "-1", '--format="%ad"', "--", str(file)],
        stdout=subprocess.PIPE,
    ).communicate()
    date_string_ = date_string.decode().strip()
    if date_string_ == "":
        modification_date = datetime.now()
    else:
        modification_date = datetime.strptime(date_string_, '"%a %b %d %X %Y %z"')

    # Start year is not 2021 or 2022
    if copyright_years[0] not in [2018, 2019, 2020, 2021, 2022]:
        return False, "Start year is not 2021 or 2022."

    # Specified year is 2021 but the file has been last modified in another later year (missing -202x)
    if (
        copyright_years[0] == 2021
        and len(copyright_years) == 1
        and copyright_years[0] < modification_date.year
    ):
        return (
            False,
            f"Specified year is 2021 but the file has been last modified in another later year (missing -202x), date last modified {date_string_}",
        )

    # Specified year is 2022 but the file has been modified in an earlier year
    if (
        copyright_years[0] == 2022
        and len(copyright_years) == 1
        and copyright_years[0] > modification_date.year
    ):
        return (
            False,
            f"Specified year is 2022 but the file has been last modified in an earlier year, date last modified {date_string_}",
        )

    # End year does not match the last modification year
    if len(copyright_years) > 1 and copyright_years[1] != modification_date.year:
        return (
            False,
            f"End year does not match the last modification year. Header has: {copyright_years[1]}; Last Modified: {modification_date.year}",
        )

    return True, ""


def check_copyright(file: Path) -> Tuple[bool, str, str]:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :return: True if the file is compliant with the checks, False otherwise.
    """
    content = file.read_text()

    for header_type, regex in REGEX_LIST:
        match = regex.match(content)
        if match is not None:
            return (*_check_copyright(file, match), header_type)

    return False, "Invalid copyright header.", "None"


if __name__ == "__main__":
    python_files = itertools.chain(
        Path("aea").glob("**/*.py"),
        Path("packages").glob("**/*.py"),
        Path("tests").glob("**/*.py"),
        Path("plugins").glob("**/*.py"),
        Path("scripts").glob("**/*.py"),
        Path("examples", "gym_ex").glob("**/*.py"),
        Path("examples", "ml_ex").glob("**/*.py"),
        [Path("setup.py")],
    )

    python_files_filtered = filter(
        lambda x: not str(x).endswith("_pb2.py"), python_files
    )
    bad_files = set()
    for path in python_files_filtered:
        print("Processing {}".format(path))
        result, message, header = check_copyright(path)
        if not result:
            bad_files.add((path, message, header))

    if len(bad_files) > 0:
        print("The following files are not well formatted:")
        print(
            "\n".join(
                map(
                    lambda x: f"File: {x[0]}\nReason: {x[1]}\nHeader: {x[2]}\n",
                    sorted(bad_files, key=lambda x: x[0]),
                )
            )
        )
        sys.exit(1)
    else:
        print("OK")
        sys.exit(0)
