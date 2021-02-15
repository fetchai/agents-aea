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
from functools import partial
from pathlib import Path
from typing import Callable, IO, Union, Dict

UNIX_LINESEP = "\n"

_open_file_builtin: Callable = partial(open, newline=UNIX_LINESEP)
_open_file_pathlib: Callable = partial(Path.open, newline=UNIX_LINESEP)

PathNameTypes = Union[int, str, bytes, Path]


def open_file(file: PathNameTypes, **kwargs: Dict) -> IO:
    r"""
    Open a file.

    Behaviour, kwargs and return type are the same for built-in 'open'
    and pathlib.Path.open, except for 'newline', which is fixed to '\n'.

    :param file: either a pathlib.Path object or the type accepted by 'open',
            i.e. a string, bytes or integer.
    :param kwargs: the keyword arguments to the wrapped function.
    :return: the IO object.
    """
    actual_wrapped_function = _open_file_builtin
    if isinstance(file, Path):
        actual_wrapped_function = _open_file_pathlib
    return actual_wrapped_function(file, **kwargs)
