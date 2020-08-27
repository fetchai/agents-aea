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
from collections import OrderedDict, UserString
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, TextIO, Union

from dotenv import load_dotenv

import yaml

logger = logging.getLogger(__name__)


def _ordered_loading(fun: Callable):
    # for pydocstyle
    def ordered_load(stream: TextIO):
        object_pairs_hook = OrderedDict

        class OrderedLoader(yaml.SafeLoader):
            """A wrapper for safe yaml loader."""

            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )
        return fun(stream, Loader=OrderedLoader)  # nosec

    return ordered_load


def _ordered_dumping(fun: Callable):
    # for pydocstyle
    def ordered_dump(data, stream=None, **kwds):
        class OrderedDumper(yaml.SafeDumper):
            """A wrapper for safe yaml loader."""

            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
            )

        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        return fun(data, stream, Dumper=OrderedDumper, **kwds)  # nosec

    return ordered_dump


@_ordered_loading
def yaml_load(*args, **kwargs) -> Dict[str, Any]:
    """
    Load a yaml from a file pointer in an ordered way.

    :return: the yaml
    """
    return yaml.load(*args, **kwargs)  # nosec


@_ordered_loading
def yaml_load_all(*args, **kwargs) -> List[Dict[str, Any]]:
    """
    Load a multi-paged yaml from a file pointer in an ordered way.

    :return: the yaml
    """
    return list(yaml.load_all(*args, **kwargs))  # nosec


@_ordered_dumping
def yaml_dump(*args, **kwargs) -> None:
    """
    Dump multi-paged yaml data to a yaml file in an ordered way.

    :return None
    """
    yaml.dump(*args, **kwargs)  # nosec


@_ordered_dumping
def yaml_dump_all(*args, **kwargs) -> None:
    """
    Dump multi-paged yaml data to a yaml file in an ordered way.

    :return None
    """
    yaml.dump_all(*args, **kwargs)  # nosec


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
        logger.debug("Trying to import {}".format(module_location))
        nextmodule = _get_module(spec)
        if nextmodule is None:
            module_location = file_location + ".py"
            spec = importlib.util.spec_from_file_location(spec_name, module_location)
            logger.debug("Trying to import {}".format(module_location))
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
