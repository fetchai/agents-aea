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
import re
import signal
import subprocess  # nosec
import sys
import time
import types
from collections import OrderedDict, UserString
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, TextIO, Union

from dotenv import load_dotenv

import yaml

from aea.configurations.base import ComponentConfiguration

logger = logging.getLogger(__name__)


def yaml_load(stream: TextIO) -> Dict[str, str]:
    """
    Load a yaml from a file pointer in an ordered way.

    :param stream: the file pointer
    :return: the yaml
    """
    # for pydocstyle
    def ordered_load(stream: TextIO, object_pairs_hook=OrderedDict):
        class OrderedLoader(yaml.SafeLoader):
            """A wrapper for safe yaml loader."""

            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )
        return yaml.load(stream, OrderedLoader)  # nosec

    return ordered_load(stream)


def yaml_dump(data, stream: TextIO) -> None:
    """
    Dump data to a yaml file in an ordered way.

    :param data: the data to be dumped
    :param stream: the file pointer
    """
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
        return yaml.dump(data, stream, OrderedDumper, **kwds)  # nosec

    ordered_dump(data, stream)


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


def load_aea_package(configuration: ComponentConfiguration) -> None:
    """
    Load the AEA package.

    It adds all the __init__.py modules into `sys.modules`.

    :param configuration: the configuration object.
    :return: None
    """
    dir_ = configuration.directory
    assert dir_ is not None

    # patch sys.modules with dummy modules
    prefix_root = "packages"
    prefix_author = prefix_root + f".{configuration.author}"
    prefix_pkg_type = prefix_author + f".{configuration.component_type.to_plural()}"
    prefix_pkg = prefix_pkg_type + f".{configuration.name}"
    sys.modules[prefix_root] = types.ModuleType(prefix_root)
    sys.modules[prefix_author] = types.ModuleType(prefix_author)
    sys.modules[prefix_pkg_type] = types.ModuleType(prefix_pkg_type)

    for subpackage_init_file in dir_.rglob("__init__.py"):
        parent_dir = subpackage_init_file.parent
        relative_parent_dir = parent_dir.relative_to(dir_)
        if relative_parent_dir == Path("."):
            # this handles the case when 'subpackage_init_file'
            # is path/to/package/__init__.py
            import_path = prefix_pkg
        else:
            import_path = prefix_pkg + "." + ".".join(relative_parent_dir.parts)

        spec = importlib.util.spec_from_file_location(import_path, subpackage_init_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[import_path] = module
        spec.loader.exec_module(module)  # type: ignore


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

    logger = fn.__globals__.get("logger", logging.getLogger(fn.__globals__["__name__"]))  # type: ignore

    return getattr(logger, logger_method)


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
