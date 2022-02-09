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
from typing import Optional, Tuple


GIT_PATH = shutil.which("git")
START_YEARS_FETCHAI = (2018, 2019, 2020, 2021)
START_YEARS_VALORY = (2021, 2022)
FETCHAI = "FetchAI"
VALORY = "Valory"
MIXED = "Mixed"

FETCHAI_REGEX = re.compile(
    r"Copyright ((20\d\d)(-20\d\d)?) Fetch.AI Limited", re.MULTILINE
)
VALORY_REGEX = re.compile(r"Copyright ((20\d\d)(-20\d\d)?) Valory AG", re.MULTILINE)


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
#   Copyright ((20\d\d)(-20\d\d)?) Valory AG
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

REGEX_LIST = [
    (FETCHAI, HEADER_REGEX_FETCHAI),
    (VALORY, HEADER_REGEX_VALORY),
    (MIXED, HEADER_REGEX_MIXED),
]


def get_modification_date(file: Path) -> datetime:
    """Returns modification date for the file."""
    date_string, _ = subprocess.Popen(  # pylint: disable=consider-using-with  # nosec
        [str(GIT_PATH), "log", "-1", '--format="%ad"', "--", str(file)],
        stdout=subprocess.PIPE,
    ).communicate()
    date_string_ = date_string.decode().strip()
    if date_string_ == "":
        return datetime.now()
    return datetime.strptime(date_string_, '"%a %b %d %X %Y %z"')


def get_year_data(match: re.Match, mixed: bool = False) -> Tuple[int, Optional[int]]:
    """Get year data from match."""

    if mixed:
        year_string, *_ = match.groups()
    else:
        _, year_string, *_ = match.groups()

    if "-" in year_string:
        return (*map(int, year_string.split("-")),)  # type: ignore
    return int(year_string), None


def _validate_years(
    file: Path,
    allowed_start_years: Tuple[int, ...],
    start_year: int,
    end_year: int,
    check_end_year: bool = True,
) -> Tuple[bool, str]:
    """
    Given a file, check if the header stuff is in place.

    Return True if the files has the encoding header and the copyright notice,
    optionally prefixed by the shebang. Return False otherwise.

    :param file: the file to check.
    :param allowed_start_years: list of allowed start years
    :param start_year: year when the file was created
    :param end_year: year when the file was last modified
    :param check_end_year: whether to validate end year or not
    :return: True if the file is compliant with the checks, False otherwise.
    """

    modification_date = get_modification_date(file)

    # Start year is not in allowed start years list
    if start_year not in allowed_start_years:
        return (
            False,
            f"Start year {start_year} is not in the list of allowed years; {allowed_start_years}.",
        )

    # Specified year is 2021 but the file has been last modified in another later year (missing -202x)
    if end_year is not None and check_end_year:

        if start_year > end_year:
            return False, "End year should be greater then start year."

        if end_year != modification_date.year:
            return (
                False,
                f"End year does not match the last modification year. Header has: {end_year}; Last Modified: {modification_date.year}",
            )

    if end_year is None and modification_date.year > start_year:
        return (
            False,
            f"Missing later year ({start_year}-20..)",
        )

    return True, ""


def _check_mixed(file: Path, content: str) -> Tuple[bool, str, str]:

    check_status, message = _validate_years(
        file,
        START_YEARS_FETCHAI,
        *get_year_data(FETCHAI_REGEX.search(content), True),  # type: ignore
        check_end_year=False,
    )
    if not check_status:
        return check_status, message, f"{MIXED}-{FETCHAI}"

    check_status, message = _validate_years(
        file, START_YEARS_VALORY, *get_year_data(VALORY_REGEX.search(content), True)  # type: ignore
    )
    if not check_status:
        return check_status, message, f"{MIXED}-{VALORY}"

    return True, "", MIXED


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
            if header_type == MIXED:
                return _check_mixed(file, content)

            elif header_type == VALORY:
                return (
                    *_validate_years(file, START_YEARS_VALORY, *get_year_data(match)),  # type: ignore
                    header_type,
                )
            elif header_type == FETCHAI:
                return (
                    *_validate_years(file, START_YEARS_FETCHAI, *get_year_data(match)),  # type: ignore
                    header_type,
                )
            break

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
