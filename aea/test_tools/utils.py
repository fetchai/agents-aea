# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Helpful utilities."""

import collections
import os
import shutil
import time
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Type,
    Union,
)


FULL_PERMISSION = 0o40777


def wait_for_condition(
    condition_checker: Callable,
    timeout: int = 2,
    error_msg: str = "Timeout",
    period: float = 0.001,
) -> None:
    """Wait for condition to occur in selected timeout."""

    start_time = time.time()
    while not condition_checker():
        time.sleep(period)
        if time.time() > start_time + timeout:
            raise TimeoutError(error_msg)


def consume(iterator: Iterable) -> None:
    """Consume the iterator"""
    collections.deque(iterator, maxlen=0)


@contextmanager
def as_context(*contexts: Any) -> Generator[None, None, None]:
    """Set contexts"""
    with ExitStack() as stack:
        consume(map(stack.enter_context, contexts))
        yield


def copy_class(cls: Type) -> Type:
    """Copy a class. Useful for testing class setup configurations"""

    # NOTE: this does not recursively deepcopy the class
    #       nor can it copy items that cannot be pickled,
    #       e.g. classes containing classmethods in __dict__.
    #       Use at your own risk.

    def is_mutable(obj: Any) -> bool:
        return isinstance(obj, (MutableSequence, MutableSet, MutableMapping))

    def deepcopy_if_mutable(mapping: Mapping[str, Any]) -> Dict[str, Any]:
        return {k: deepcopy(v) if is_mutable(v) else v for k, v in mapping.items()}

    return type(
        f"CopyOf{cls.__name__}",
        (cls, *cls.__bases__),
        deepcopy_if_mutable(cls.__dict__),
    )


def remove_test_directory(directory: Union[str, Path], retries: int = 3) -> bool:
    """Destroy a directory once tests are done, change permissions if needed.

    Note that on Windows directories and files that are open cannot be deleted.

    :param directory: directory to be deleted
    :param retries: number of re-attempts
    :return: whether the directory was successfully deleted
    """

    permission = os.stat(directory).st_mode
    while os.path.exists(directory) and retries:
        try:
            os.chmod(directory, FULL_PERMISSION)  # nosec
            shutil.rmtree(directory)
        except Exception:  # pylint: disable=broad-except
            retries -= 1
            time.sleep(1)
        finally:
            if os.path.exists(directory):
                os.chmod(directory, permission)
    return not os.path.exists(directory)
