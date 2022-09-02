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
"""Miscellaneous helpers."""
import builtins
import contextlib
import datetime
import importlib.util
import logging
import os
import platform
import re
import shutil
import signal
import subprocess  # nosec
import sys
import time
import types
from collections import OrderedDict, UserString, defaultdict, deque
from collections.abc import Mapping
from copy import copy
from functools import wraps
from importlib.machinery import ModuleSpec
from pathlib import Path
from threading import RLock
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from dotenv import load_dotenv
from packaging.version import Version

from aea.common import PathLike
from aea.exceptions import enforce


STRING_LENGTH_LIMIT = 128
SIMPLE_ID_REGEX = rf"[a-zA-Z_][a-zA-Z0-9_]{{0,{STRING_LENGTH_LIMIT - 1}}}"
ISO_8601_DATE_FORMAT = "%Y-%m-%d"

IPFS_HASH_LENGTH_LIMIT_V0 = 46
IPFS_HASH_LENGTH_LIMIT_V1 = 59
IPFS_HASH_REGEX_V0 = rf"Qm[a-zA-Z0-9]{{{IPFS_HASH_LENGTH_LIMIT_V0 - 2}}}"
IPFS_HASH_REGEX_v1 = rf"ba[a-zA-Z0-9]{{{IPFS_HASH_LENGTH_LIMIT_V1 - 2}}}"
IPFS_HASH_REGEX = f"(({IPFS_HASH_REGEX_V0})|({IPFS_HASH_REGEX_v1}))"


_default_logger = logging.getLogger(__name__)


def _get_module(spec: ModuleSpec) -> Optional[types.ModuleType]:
    """Try to execute a module. Return None if the attempt fail."""
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return module
    except Exception:  # pylint: disable=broad-except
        return None


def locate(path: str) -> Any:
    """Locate an object by name or dotted save_path, importing as necessary."""
    parts = [part for part in path.split(".") if part]
    module, n = None, 0
    while n < len(parts):
        file_location = os.path.join(*parts[: n + 1])
        spec_name = ".".join(parts[: n + 1])
        module_location = os.path.join(file_location, "__init__.py")
        spec = importlib.util.spec_from_file_location(spec_name, module_location)
        _default_logger.debug("Trying to import {}".format(module_location))
        nextmodule = _get_module(cast(ModuleSpec, spec))
        if nextmodule is None:
            module_location = file_location + ".py"
            spec = importlib.util.spec_from_file_location(spec_name, module_location)
            _default_logger.debug("Trying to import {}".format(module_location))
            nextmodule = _get_module(cast(ModuleSpec, spec))

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

    :param dotted_path: the dotted save_path of the package/module.
    :param filepath: the file to the package/module.
    :return: module type
    :raises ValueError: if the filepath provided is not a module.  # noqa: DAR402
    :raises Exception: if the execution of the module raises exception.  # noqa: DAR402
    """
    spec = importlib.util.spec_from_file_location(dotted_path, str(filepath))
    module = importlib.util.module_from_spec(cast(ModuleSpec, spec))
    spec.loader.exec_module(module)  # type: ignore
    return module


def load_env_file(env_file: str) -> None:
    """
    Load the content of the environment file into the process environment.

    :param env_file: save_path to the env file.
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
    """
    if os.name == "posix":
        process.send_signal(signal.SIGINT)  # type: ignore  # pylint: disable=no-member
    elif os.name == "nt":
        process.send_signal(signal.CTRL_C_EVENT)  # type: ignore   # pylint: disable=no-member
    else:
        raise ValueError("Other platforms not supported.")


def win_popen_kwargs() -> dict:
    """
    Return kwargs to start a process in windows with new process group.

    Help to handle ctrl c properly.
    Return empty dict if platform is not win32

    :return: windows popen kwargs
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
    Send ctrl-C cross-platform to terminate a subprocess.

    :param process: the process to send the signal to.
    :param kill_group: whether or not to kill group
    """
    if platform.system() == "Windows":
        if process.stdin:  # cause ctrl-c event will be handled with stdin
            process.stdin.close()
        os.kill(process.pid, signal.CTRL_C_EVENT)  # type: ignore   # pylint: disable=no-member
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

    def __init__(self, seq: Union[UserString, str]) -> None:
        """Initialize a regex constrained string."""
        super().__init__(seq)

        if not self.REGEX.fullmatch(self.data):
            self._handle_no_match()

    def _handle_no_match(self) -> None:
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

    >>> SimpleId("an identifier")
    Traceback (most recent call last):
    ...
    ValueError: Value an identifier does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

    >>> SimpleId("")
    Traceback (most recent call last):
    ...
    ValueError: Value  does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')
    """

    REGEX = re.compile(SIMPLE_ID_REGEX)


class IPFSHash(RegexConstrainedString):
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

    >>> SimpleId("an identifier")
    Traceback (most recent call last):
    ...
    ValueError: Value an identifier does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')

    >>> SimpleId("")
    Traceback (most recent call last):
    ...
    ValueError: Value  does not match the regular expression re.compile('[a-zA-Z_][a-zA-Z0-9_]{0,127}')
    """

    REGEX = re.compile(IPFS_HASH_REGEX)


SimpleIdOrStr = Union[SimpleId, str]
IPFSHashOrStr = Union[IPFSHash, str]


@contextlib.contextmanager
def cd(path: PathLike) -> Generator:  # pragma: nocover
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

    Get logger in `fn` definition module or creates logger is module.__name__.
    Or return logger_method if it's callable.

    :param fn: function to get logger for.
    :param logger_method: logger name or callable.

    :return: callable to write log with
    """
    if callable(logger_method):  # pragma: nocover
        return logger_method

    logger_ = fn.__globals__.get("logger", logging.getLogger(fn.__globals__["__name__"]))  # type: ignore

    return getattr(logger_, logger_method)


def try_decorator(
    error_message: str, default_return: Callable = None, logger_method: Any = "error"
) -> Callable:
    """
    Run function, log and return default value on exception.

    Does not support async or coroutines!

    :param error_message: message template with one `{}` for exception
    :param default_return: value to return on exception, by default None
    :param logger_method: name of the logger method or callable to print logs
    :return: the callable
    """

    # for pydocstyle
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Callable:
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # pylint: disable=broad-except  # pragma: no cover  # generic code
                if kwargs.get("raise_on_try", False):
                    raise e
                if error_message:
                    log = get_logger_method(fn, logger_method)
                    log(error_message.format(e))
                return cast(Callable, default_return)

        return wrapper

    return decorator


class MaxRetriesError(Exception):
    """Exception for retry decorator."""


def retry_decorator(
    number_of_retries: int,
    error_message: str,
    delay: float = 0,
    logger_method: str = "error",
) -> Callable:
    """
    Run function with several attempts.

    Does not support async or coroutines!

    :param number_of_retries: amount of attempts
    :param error_message: message template with one `{}` for exception
    :param delay: number of seconds to sleep between retries. default 0
    :param logger_method: name of the logger method or callable to print logs
    :return: the callable
    """

    # for pydocstyle
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Callable:
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
def exception_log_and_reraise(log_method: Callable, message: str) -> Generator:
    """
    Run code in context to log and re raise exception.

    :param log_method: function to print log
    :param message: message template to add error text.
    :yield: the generator
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


def recursive_update(
    to_update: Dict,
    new_values: Dict,
    allow_new_values: bool = False,
) -> None:
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
    :param allow_new_values: whether or not to allow new values.
    """
    for key, value in new_values.items():
        if (not allow_new_values) and key not in to_update:
            raise ValueError(
                f"Key '{key}' is not contained in the dictionary to update."
            )

        if key not in to_update and allow_new_values:
            to_update[key] = value
            continue

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
            recursive_update(value_to_update, value, allow_new_values)
        else:
            to_update[key] = value


def perform_dict_override(
    component_id: Any,
    overrides: Dict,
    updated_configuration: Dict,
    new_configuration: Dict,
) -> None:
    """
    Perform recursive dict override.

    :param component_id: Component ID for which the updated will be performed
    :param overrides: A dictionary containing mapping for Component ID -> List of paths
    :param updated_configuration: Configuration which needs to be updated
    :param new_configuration: Configuration from which the method will perform the update
    """
    for path in overrides[component_id]:

        will_be_updated = updated_configuration[component_id]
        update = new_configuration[component_id]

        *params, update_param = path
        for param in params:
            will_be_updated = will_be_updated[param]
            update = update[param]

        will_be_updated[update_param] = update[update_param]


def _get_aea_logger_name_prefix(module_name: str, agent_name: str) -> str:
    """
    Get the logger name prefix.

    It consists of a dotted save_path with:
    - the name of the package, 'aea';
    - the agent name;
    - the rest of the dotted save_path.

    >>> _get_aea_logger_name_prefix("aea.save_path.to.package", "myagent")
    'aea.myagent.save_path.to.package'

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
    # compute both roots and inverse adjacent list in one pass.
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
    queue.extendleft(sorted(roots))  # type: ignore
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

    def __init__(self, func: Callable) -> None:
        """Init cached property."""
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__
        self.lock = RLock()

    def __set_name__(self, _: Any, name: Any) -> None:
        """Set name."""
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same cached_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def __get__(self, instance: Any, _: Optional[Any] = None) -> Any:
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


def dict_to_path_value(
    data: Mapping, path: Optional[List] = None
) -> Iterable[Tuple[List[str], Any]]:
    """Convert dict to sequence of terminal path build of  keys and value."""
    path = path or []
    for key, value in data.items():
        if isinstance(value, Mapping) and value:
            # terminal value
            for p, v in dict_to_path_value(value, path + [key]):
                yield p, v
        else:
            yield path + [key], value


def parse_datetime_from_str(date_string: str) -> datetime.datetime:
    """Parse datetime from string."""
    result = datetime.datetime.strptime(date_string, ISO_8601_DATE_FORMAT)
    result = result.replace(tzinfo=datetime.timezone.utc)
    return result


class CertRequest:
    """Certificate request for proof of representation."""

    def __init__(
        self,
        public_key: str,
        identifier: SimpleIdOrStr,
        ledger_id: SimpleIdOrStr,
        not_before: str,
        not_after: str,
        message_format: str,
        save_path: str,
    ) -> None:
        """
        Initialize the certificate request.

        :param public_key: the public key, or the key id.
        :param identifier: certificate identifier.
        :param ledger_id: ledger identifier the request is referring to.
        :param not_before: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
        :param not_after: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
        :param message_format: message format used for signing
        :param save_path: the save_path where to save the certificate.
        """
        self._key_identifier: Optional[str] = None
        self._public_key: Optional[str] = None
        self._identifier = str(SimpleId(identifier))
        self._ledger_id = str(SimpleId(ledger_id))
        self._not_before_string = not_before
        self._not_after_string = not_after
        self._not_before = self._parse_datetime(not_before)
        self._not_after = self._parse_datetime(not_after)
        self._message_format = message_format
        self._save_path = Path(save_path)

        self._parse_public_key(public_key)
        self._check_validation_boundaries()

    @classmethod
    def _parse_datetime(cls, obj: Union[str, datetime.datetime]) -> datetime.datetime:
        """
        Parse datetime string.

        It is expected to follow ISO 8601.

        :param obj: the input to parse.
        :return: a datetime.datetime instance.
        """
        result = (
            parse_datetime_from_str(obj)  # type: ignore
            if isinstance(obj, str)
            else obj
        )
        enforce(result.microsecond == 0, "Microsecond field not allowed.")
        return result

    def _check_validation_boundaries(self) -> None:
        """
        Check the validation boundaries are consistent.

        Namely, that not_before < not_after.
        """
        enforce(
            self._not_before < self._not_after,
            f"Inconsistent certificate validity period: 'not_before' field '{self._not_before_string}' is not before than 'not_after' field '{self._not_after_string}'",
            ValueError,
        )

    def _parse_public_key(self, public_key_str: str) -> None:
        """
        Parse public key from string.

        It first tries to parse it as an identifier,
        and in case of failure as a sequence of hexadecimals, starting with "0x".

        :param public_key_str: the public key
        """
        with contextlib.suppress(ValueError):
            # if this raises ValueError, we don't return
            self._key_identifier = str(SimpleId(public_key_str))
            return

        with contextlib.suppress(ValueError):
            # this raises ValueError if the input is not a valid hexadecimal string.
            int(public_key_str, 16)
            self._public_key = public_key_str
            return

        enforce(
            False,
            f"Public key field '{public_key_str}' is neither a valid identifier nor an address.",
            exception_class=ValueError,
        )

    @property
    def public_key(self) -> Optional[str]:
        """Get the public key."""
        return self._public_key

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def key_identifier(self) -> Optional[str]:
        """Get the key identifier."""
        return self._key_identifier

    @property
    def identifier(self) -> str:
        """Get the identifier."""
        return self._identifier

    @property
    def not_before_string(self) -> str:
        """Get the not_before field as string."""
        return self._not_before_string

    @property
    def not_after_string(self) -> str:
        """Get the not_after field as string."""
        return self._not_after_string

    @property
    def not_before(self) -> datetime.datetime:
        """Get the not_before field."""
        return self._not_before

    @property
    def not_after(self) -> datetime.datetime:
        """Get the not_after field."""
        return self._not_after

    @property
    def message_format(self) -> str:
        """Get the message format."""
        return self._message_format

    @property
    def save_path(self) -> Path:
        """
        Get the save path for the certificate.

        Note: if the path is *not* absolute, then
        the actual save path might depend on the context.

        :return: the save path
        """
        return self._save_path

    def get_absolute_save_path(self, path_prefix: Optional[PathLike] = None) -> Path:
        """
        Get the absolute save path.

        If save_path is an absolute path, then the prefix is ignored.
        Otherwise, the path prefix is prepended.

        :param path_prefix: the (absolute) path to prepend to the save path.
        :return: the actual save path.
        """
        path_prefix = (
            Path(path_prefix).absolute() if path_prefix is not None else Path.cwd()
        )
        return (
            self.save_path
            if self.save_path.is_absolute()
            else path_prefix / self.save_path
        )

    @property
    def public_key_or_identifier(self) -> str:
        """Get the public key or identifier."""
        if (self.public_key is None and self.key_identifier is None) or (
            self.public_key is not None and self.key_identifier is not None
        ):
            raise ValueError(  # pragma: nocover
                "Exactly one of key_identifier or public_key can be specified."
            )
        if self.public_key is not None:
            result = self.public_key
        elif self.key_identifier is not None:
            result = self.key_identifier
        return result

    def get_message(self, public_key: str) -> bytes:  # pylint: disable=no-self-use
        """Get the message to sign."""
        message = self.construct_message(
            public_key,
            self.identifier,
            self.not_before_string,
            self.not_after_string,
            self.message_format,
        )
        return message

    @classmethod
    def construct_message(
        cls,
        public_key: str,
        identifier: SimpleIdOrStr,
        not_before_string: str,
        not_after_string: str,
        message_format: str,
    ) -> bytes:
        """
        Construct message for singning.

        :param public_key: the public key
        :param identifier: identifier to be signed
        :param not_before_string: signature not valid before
        :param not_after_string: signature not valid after
        :param message_format: message format used for signing
        :return: the message
        """
        message = message_format.format(
            public_key=public_key,
            identifier=str(identifier),
            not_before=not_before_string,
            not_after=not_after_string,
        )
        return message.encode("ascii")

    def get_signature(self, path_prefix: Optional[PathLike] = None) -> str:
        """
        Get signature from save_path.

        :param path_prefix: the path prefix to be prepended to save_path. Defaults to cwd.
        :return: the signature.
        """
        save_path = self.get_absolute_save_path(path_prefix)
        if not Path(save_path).is_file():
            raise Exception(  # pragma: no cover
                f"cert_request 'save_path' field {save_path} is not a file. "
                "Please ensure that 'issue-certificates' command is called beforehand."
            )
        signature = bytes.fromhex(Path(save_path).read_bytes().decode("ascii")).decode(
            "ascii"
        )
        return signature

    @property
    def json(self) -> Dict:
        """Compute the JSON representation."""
        result = dict(
            identifier=self.identifier,
            ledger_id=self.ledger_id,
            not_before=self._not_before_string,
            not_after=self._not_after_string,
            public_key=self.public_key_or_identifier,
            message_format=self.message_format,
            save_path=str(self.save_path),
        )
        return result

    @classmethod
    def from_json(cls, obj: Dict) -> "CertRequest":
        """Compute the JSON representation."""
        if "message_format" not in obj:  # pragma: nocover
            # for backwards compatibility
            obj["message_format"] = "{public_key}"
        return cls(**obj)

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, CertRequest)
            and self.identifier == other.identifier
            and self.ledger_id == other.ledger_id
            and self.public_key == other.public_key
            and self.key_identifier == other.key_identifier
            and self.not_after == other.not_after
            and self.not_before == other.not_before
            and self.message_format == other.message_format
            and self.save_path == other.save_path
        )


def compute_specifier_from_version(version: Version) -> str:
    """
    Compute the specifier set from a version.

    version specifier is:  >=major.minor.0, <next_major.0.0

    :param version: the version
    :return: the specifier set
    """
    new_major_low = version.major
    new_major_high = version.major + 1
    new_minor_low = version.minor
    new_minor_high = new_minor_low + 1
    if new_major_low == 0:
        lower_bound = Version(f"{new_major_low}.{new_minor_low}.0")
        lower_bound = lower_bound if lower_bound < version else version
        upper_bound = Version(f"{new_major_low}.{new_minor_high}.0")
    else:
        lower_bound = Version(f"{new_major_low}.{version.minor}.0")
        lower_bound = lower_bound if lower_bound < version else version
        upper_bound = Version(f"{new_major_high}.0.0")
    specifier_set = f">={lower_bound}, <{upper_bound}"
    return specifier_set


def decorator_with_optional_params(decorator: Callable) -> Callable:
    """
    Make a decorator usable either with or without parameters.

    In other words, if a decorator "mydecorator" is decorated with this decorator,
    It can be used both as:

    @mydecorator
    def myfunction():
        ...

    or as:

    @mydecorator(arg1, kwarg1="value")
    def myfunction():
        ...

    :param decorator: a decorator callable
    :return: a decorator callable
    """

    @wraps(decorator)
    def new_decorator(*args: Any, **kwargs: Any) -> Callable:
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            return decorator(args[0])

        def final_decorator(real_function: Callable) -> Callable:
            return decorator(real_function, *args, **kwargs)

        return final_decorator

    return new_decorator


def delete_directory_contents(directory: Path) -> None:
    """Delete the content of a directory, without deleting it."""
    enforce(directory.is_dir(), f"Path '{directory}' must be a directory.")
    for filename in directory.iterdir():
        if filename.is_file() or filename.is_symlink():
            filename.unlink()
        elif filename.is_dir():
            shutil.rmtree(str(filename), ignore_errors=False)


def prepend_if_not_absolute(path: PathLike, prefix: PathLike) -> PathLike:
    """
    Prepend a path with a prefix, but only if not absolute

    :param path: the path to process.
    :param prefix: the path prefix.
    :return: the same path if absolute, else the prepended path.
    """
    return path if Path(path).is_absolute() else Path(prefix) / path
