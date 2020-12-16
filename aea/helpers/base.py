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
"""Miscellaneous helpers."""
import builtins
import contextlib
import importlib.util
import logging
import os
import platform
import re
import signal
import subprocess  # nosec
import sys
import time
import types
from collections import OrderedDict, UserString, defaultdict, deque
from copy import copy
from functools import wraps
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Deque, Dict, List, Set, TypeVar, Union

from dotenv import load_dotenv

from aea.exceptions import enforce


STRING_LENGTH_LIMIT = 128

_default_logger = logging.getLogger(__name__)


def _get_module(spec):
    """Try to execute a module. Return None if the attempt fail."""
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:  # pylint: disable=broad-except
        return None


def locate(path: str) -> Any:
    """Locate an object by name or dotted path, importing as necessary."""
    parts = [part for part in path.split(".") if part]
    module, n = None, 0
    while n < len(parts):
        file_location = os.path.join(*parts[: n + 1])
        spec_name = ".".join(parts[: n + 1])
        module_location = os.path.join(file_location, "__init__.py")
        spec = importlib.util.spec_from_file_location(spec_name, module_location)
        _default_logger.debug("Trying to import {}".format(module_location))
        nextmodule = _get_module(spec)
        if nextmodule is None:
            module_location = file_location + ".py"
            spec = importlib.util.spec_from_file_location(spec_name, module_location)
            _default_logger.debug("Trying to import {}".format(module_location))
            nextmodule = _get_module(spec)

        if nextmodule:
            module, n = nextmodule, n + 1
        else:  # pragma: nocover
            break
    if module:
        object_ = module
    else:
        object_ = builtins
    for part in parts[n:]:
        try:
            object_ = getattr(object_, part)
        except AttributeError:
            return None
    return object_


def load_module(dotted_path: str, filepath: Path) -> types.ModuleType:
    """
    Load a module.

    :param dotted_path: the dotted path of the package/module.
    :param filepath: the file to the package/module.
    :return: None
    :raises ValueError: if the filepath provided is not a module.
    :raises Exception: if the execution of the module raises exception.
    """
    spec = importlib.util.spec_from_file_location(dotted_path, str(filepath))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def load_env_file(env_file: str):
    """
    Load the content of the environment file into the process environment.

    :param env_file: path to the env file.
    :return: None.
    """
    load_dotenv(dotenv_path=Path(env_file), override=False)


def sigint_crossplatform(process: subprocess.Popen) -> None:  # pragma: nocover
    """
    Send a SIGINT, cross-platform.

    The reason is because the subprocess module
    doesn't have an API to send a SIGINT-like signal
    both on Posix and Windows with a single method.

    However, a subprocess.Popen class has the method
    'send_signal' that gives more flexibility in this terms.

    :param process: the process to send the signal to.
    :return: None
    """
    if os.name == "posix":
        process.send_signal(signal.SIGINT)  # pylint: disable=no-member
    elif os.name == "nt":
        process.send_signal(signal.CTRL_C_EVENT)  # pylint: disable=no-member
    else:
        raise ValueError("Other platforms not supported.")


def win_popen_kwargs() -> dict:
    """
    Return kwargs to start a process in windows with new process group.

    Help to handle ctrl c properly.
    Return empty dict if platform is not win32
    """
    kwargs: dict = {}

    if sys.platform == "win32":  # pragma: nocover
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    return kwargs


def send_control_c(
    process: subprocess.Popen, kill_group: bool = False
) -> None:  # pragma: nocover # cause platform dependent
    """
    Send ctrl-C crossplatform to terminate a subprocess.

    :param process: the process to send the signal to.

    :return: None
    """
    if platform.system() == "Windows":
        if process.stdin:  # cause ctrl-c event will be handled with stdin
            process.stdin.close()
        os.kill(process.pid, signal.CTRL_C_EVENT)  # pylint: disable=no-member
    elif kill_group:
        pgid = os.getpgid(process.pid)
        os.killpg(pgid, signal.SIGINT)
    else:
        os.kill(process.pid, signal.SIGINT)


class RegexConstrainedString(UserString):
    """
    A string that is constrained by a regex.

    The default behaviour is to match anything.
    Subclass this class and change the 'REGEX' class
    attribute to implement a different behaviour.
    """

    REGEX = re.compile(".*", flags=re.DOTALL)

    def __init__(self, seq):
        """Initialize a regex constrained string."""
        super().__init__(seq)

        if not self.REGEX.match(self.data):
            self._handle_no_match()

    def _handle_no_match(self):
        raise ValueError(
            "Value {data} does not match the regular expression {regex}".format(
                data=self.data, regex=self.REGEX
            )
        )


class SimpleId(RegexConstrainedString):
    """
    A simple identifier.

    The allowed strings are all the strings that:
    - have at least length 1
    - have at most length 128
    - the first character must be between a-z,A-Z or underscore
    - the other characters must be either the above or digits.

    Examples of allowed strings:
    >>> SimpleId("an_identifier")
    'an_identifier'

    Examples of not allowed strings:
    >>> SimpleId("0an_identifier")
    Traceback (most recent call last):
    ...
    ValueError: Value 0an_identifier does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

    >>> SimpleId("")
    Traceback (most recent call last):
    ...
    ValueError: Value  does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')
    """

    REGEX = re.compile(fr"[a-zA-Z_][a-zA-Z0-9_]{{0,{STRING_LENGTH_LIMIT - 1}}}")


SimpleIdOrStr = Union[SimpleId, str]


@contextlib.contextmanager
def cd(path):  # pragma: nocover
    """Change working directory temporarily."""
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


def get_logger_method(fn: Callable, logger_method: Union[str, Callable]) -> Callable:
    """
    Get logger method for function.

    Get logger in `fn` definion module or creates logger is module.__name__.
    Or return logger_method if it's callable.

    :param fn: function to get logger for.
    :param logger_method: logger name or callable.

    :return: callable to write log with
    """
    if callable(logger_method):  # pragma: nocover
        return logger_method

    logger_ = fn.__globals__.get("logger", logging.getLogger(fn.__globals__["__name__"]))  # type: ignore

    return getattr(logger_, logger_method)


def try_decorator(error_message: str, default_return=None, logger_method="error"):
    """
    Run function, log and return default value on exception.

    Does not support async or coroutines!

    :param error_message: message template with one `{}` for exception
    :param default_return: value to return on exception, by default None
    :param logger_method: name of the logger method or callable to print logs
    """

    # for pydocstyle
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # pylint: disable=broad-except  # pragma: no cover  # generic code
                if error_message:
                    log = get_logger_method(fn, logger_method)
                    log(error_message.format(e))
                return default_return

        return wrapper

    return decorator


class MaxRetriesError(Exception):
    """Exception for retry decorator."""


def retry_decorator(
    number_of_retries: int, error_message: str, delay: float = 0, logger_method="error"
):
    """
    Run function with several attempts.

    Does not support async or coroutines!

    :param number_of_retries: amount of attempts
    :param error_message: message template with one `{}` for exception
    :param delay: num of seconds to sleep between retries. default 0
    :param logger_method: name of the logger method or callable to print logs
    """

    # for pydocstyle
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            log = get_logger_method(fn, logger_method)
            for retry in range(number_of_retries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:  # pylint: disable=broad-except  # pragma: no cover  # generic code
                    if error_message:
                        log(error_message.format(retry=retry + 1, error=e))
                    if delay:
                        time.sleep(delay)
            raise MaxRetriesError(number_of_retries)

        return wrapper

    return decorator


@contextlib.contextmanager
def exception_log_and_reraise(log_method: Callable, message: str):
    """
    Run code in context to log and re raise exception.

    :param log_method: function to print log
    :param message: message template to add error text.
    """
    try:
        yield
    except BaseException as e:  # pylint: disable=broad-except  # pragma: no cover  # generic code
        log_method(message.format(e))
        raise


def _is_dict_like(obj: Any) -> bool:
    """
    Check whether an object is dict-like (i.e. either dict or OrderedDict).

    :param obj: the object to test.
    :return: True if the object is dict-like, False otherwise.
    """
    return type(obj) in {dict, OrderedDict}


def recursive_update(to_update: Dict, new_values: Dict) -> None:
    """
    Update a dictionary by replacing conflicts with the new values.

    It does side-effects to the first dictionary.

    >>> to_update = dict(a=1, b=2, subdict=dict(subfield1=1))
    >>> new_values = dict(b=3, subdict=dict(subfield1=2))
    >>> recursive_update(to_update, new_values)
    >>> to_update
    {'a': 1, 'b': 3, 'subdict': {'subfield1': 2}}

    :param to_update: the dictionary to update.
    :param new_values: the dictionary of new values to replace.
    :return: None
    """
    for key, value in new_values.items():
        if key not in to_update:
            raise ValueError(
                f"Key '{key}' is not contained in the dictionary to update."
            )

        value_to_update = to_update[key]
        value_type = type(value)
        value_to_update_type = type(value_to_update)
        both_are_dict = _is_dict_like(value) and _is_dict_like(value_to_update)
        if (
            not both_are_dict
            and value_type != value_to_update_type
            and value is not None
            and value_to_update is not None
        ):
            raise ValueError(
                f"Trying to replace value '{value_to_update}' with value '{value}' which is of different type."
            )

        if both_are_dict:
            recursive_update(value_to_update, value)
        else:
            to_update[key] = value


def _get_aea_logger_name_prefix(module_name: str, agent_name: str) -> str:
    """
    Get the logger name prefix.

    It consists of a dotted path with:
    - the name of the package, 'aea';
    - the agent name;
    - the rest of the dotted path.

    >>> _get_aea_logger_name_prefix("aea.path.to.package", "myagent")
    'aea.myagent.path.to.package'

    :param module_name: the module name.
    :param agent_name: the agent name.
    :return: the logger name prefix.
    """
    module_name_parts = module_name.split(".")
    root = module_name_parts[0]
    postfix = module_name_parts[1:]
    return ".".join([root, agent_name, *postfix])


T = TypeVar("T")


def find_topological_order(adjacency_list: Dict[T, Set[T]]) -> List[T]:
    """
    Compute the topological order of a graph (using Kahn's algorithm).

    :param adjacency_list: the adjacency list of the graph.
    :return: the topological order for the graph (as a sequence of nodes)
    :raises ValueError: if the graph contains a cycle.
    """
    # compute inverse adjacency list and the roots of the DAG.
    adjacency_list = copy(adjacency_list)
    visited: Set[T] = set()
    roots: Set[T] = set()
    inverse_adjacency_list: Dict[T, Set[T]] = defaultdict(set)
    # compute both roots and inv. adj. list in one pass.
    for start_node, end_nodes in adjacency_list.items():
        if start_node not in visited:
            roots.add(start_node)
        visited.update([start_node, *end_nodes])
        for end_node in end_nodes:
            roots.discard(end_node)
            inverse_adjacency_list[end_node].add(start_node)

    # compute the topological order
    queue: Deque[T] = deque()
    order = []
    queue.extendleft(sorted(roots))
    while len(queue) > 0:
        current = queue.pop()
        order.append(current)
        next_nodes = adjacency_list.get(current, set())
        for node in next_nodes:
            inverse_adjacency_list[node].discard(current)
            if len(inverse_adjacency_list[node]) == 0:
                queue.append(node)

        # remove all the edges
        adjacency_list[current] = set()

    if any(len(edges) > 0 for edges in inverse_adjacency_list.values()):
        raise ValueError("Graph has at least one cycle.")

    return order


def reachable_nodes(
    adjacency_list: Dict[T, Set[T]], starting_nodes: Set[T]
) -> Dict[T, Set[T]]:
    """
    Find the reachable subgraph induced by a set of starting nodes.

    :param adjacency_list: the adjacency list of the full graph.
    :param starting_nodes: the starting nodes of the new graph.
    :return: the adjacency list of the subgraph.
    """
    all_nodes = set()
    for node, nodes in adjacency_list.items():
        all_nodes.add(node)
        all_nodes.update(nodes)
    enforce(
        all(s in all_nodes for s in starting_nodes),
        f"These starting nodes are not in the set of nodes: {starting_nodes.difference(all_nodes)}",
    )
    visited: Set[T] = set()
    result: Dict[T, Set[T]] = {start_node: set() for start_node in starting_nodes}
    queue: Deque[T] = deque()
    queue.extend(starting_nodes)
    while len(queue) > 0:
        current = queue.pop()
        if current in visited or current not in adjacency_list:
            continue
        successors = adjacency_list.get(current, set())
        result.setdefault(current, set()).update(successors)
        queue.extendleft(successors)
        visited.add(current)
    return result


_NOT_FOUND = object()


# copied from python3.8 functools
class cached_property:  # pragma: nocover
    """Cached property from python3.8 functools."""

    def __init__(self, func):
        """Init cached property."""
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__
        self.lock = RLock()

    def __set_name__(self, _, name):
        """Set name."""
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same cached_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def __get__(self, instance, _=None):
        """Get instance."""
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use cached_property instance without calling __set_name__ on it."
            )
        try:
            cache = instance.__dict__
        except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.attrname!r} property."
            )
            raise TypeError(msg) from None
        val = cache.get(self.attrname, _NOT_FOUND)
        if val is _NOT_FOUND:
            with self.lock:
                # check if another thread filled cache while we awaited lock
                val = cache.get(self.attrname, _NOT_FOUND)
                if val is _NOT_FOUND:
                    val = self.func(instance)
                    try:
                        cache[self.attrname] = val
                    except TypeError:
                        msg = (
                            f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                            f"does not support item assignment for caching {self.attrname!r} property."
                        )
                        raise TypeError(msg) from None
        return val


def ensure_dir(dir_path: str) -> None:
    """Check if dir_path is a directory or create it."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    else:
        enforce(os.path.isdir(dir_path), f"{dir_path} is not a directory!")
