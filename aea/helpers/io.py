# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

r"""
Wrapper over built-in "open" function.

This module contains a wrapper to the built-in 'open'
function, the 'open_file' function, that fixes the
keyword argument 'newline' to be equal to "\n" (the UNIX line separator).
This will force the line separator to be "\n" both
for incoming and outgoing data.

The reason of this is that files written in an AEA package
need to have "\n" as line separator, on all platforms. Otherwise,
the fingerprint of the packages involved would change across platforms
just because the line separators are replaced.

For instance, the 'open' function on Windows, by default (newline=None),
would replace the line separators "\n" with "\r\n".
This has an impact in the computation of the fingerprint.

Hence, any usage of file system functionalities
should either use 'open_file', or set 'newline="\n"' when
calling the 'open' or the 'pathlib.Path.open' functions.
"""
import collections
import csv
from functools import partial
from pathlib import Path
from typing import Callable, Dict, Optional, TextIO, Union


UNIX_LINESEP = "\n"

_open_file_builtin: Callable = partial(open, newline=UNIX_LINESEP)
_open_file_pathlib: Callable = partial(Path.open, newline=UNIX_LINESEP)

PathNameTypes = Union[int, str, bytes, Path]


def open_file(
    file: PathNameTypes,
    mode: str = "r",
    buffering: int = -1,
    encoding: Optional[str] = None,
    errors: Optional[str] = None,
) -> TextIO:
    r"""
    Open a file.

    Behaviour, kwargs and return type are the same for built-in 'open'
    and pathlib.Path.open, except for 'newline', which is fixed to '\n'.

    For more details on the keyword arguments, please refer
    to the documentation for the built-in 'open':

        https://docs.python.org/3/library/functions.html#open

    :param file: either a pathlib.Path object or the type accepted by 'open',
            i.e. a string, bytes or integer.
    :param mode: the mode in which the file is opened.
    :param buffering: the buffering policy.
    :param encoding: the name of the encoding used to decode or encode the file.
    :param errors: how encoding errors are to be handled
    :return: the IO object.
    """
    if "b" in mode:
        raise ValueError("This function can only work in text mode.")
    actual_wrapped_function = _open_file_builtin
    if isinstance(file, Path):
        actual_wrapped_function = _open_file_pathlib
    return actual_wrapped_function(
        file, mode=mode, buffering=buffering, encoding=encoding, errors=errors
    )


def to_csv(data: Dict[str, str], path: Path) -> None:
    """Outputs a dictionary to CSV."""
    try:
        ordered = collections.OrderedDict(sorted(data.items()))
        with open(path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(ordered.items())
    except IOError:
        print("I/O error")


def from_csv(path: Path) -> Dict[str, str]:
    """Load a CSV into a dictionary."""
    result = collections.OrderedDict({})  # type: Dict[str, str]
    with open(path, "r") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if len(row) != 2:
                raise ValueError("Length of the row should be 2.")

            key, value = row
            result[key] = value
    return result
