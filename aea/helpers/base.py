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
import importlib.util
import logging
import os
import sys
import types
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)


def _get_module(spec):
    """Try to execute a module. Return None if the attempt fail."""
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def locate(path):
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
        else:
            break
    if module:
        object = module
    else:
        object = builtins
    for part in parts[n:]:
        try:
            object = getattr(object, part)
        except AttributeError:
            return None
    return object


def load_init_modules(directory: Path) -> Dict[str, types.ModuleType]:
    """Load __init__.py modules of a directory, recursively."""
    if not directory.exists() or not directory.is_dir():
        raise ValueError("The provided path does not exists or it is not a directory.")
    result = {}  # type: Dict[str, types.ModuleType]
    package_root_directory = directory
    for init_module_path in directory.rglob("__init__.py"):
        relative_path_directory = init_module_path.relative_to(
            package_root_directory
        ).parent
        # relative_path_directory is "." if __init__.py is in the root of the package directory,
        # and a path when it is a subpackage. We handle these cases separately.
        relative_dotted_path = (
            str(relative_path_directory).replace(os.path.sep, ".")
            if str(relative_path_directory) != "."
            else ""
        )
        init_module = load_module(relative_dotted_path, init_module_path)
        result[relative_dotted_path] = init_module

    return result


class _SysModules:
    """Helper class that load modules to sys.modules."""

    __rlock = RLock()

    @staticmethod
    @contextmanager
    def load_modules(modules: List[Tuple[str, types.ModuleType]]) -> None:
        """
        Load modules as a context manager.

        :param modules: a list of pairs (import path, module object).
        :return: None.
        """
        with _SysModules.__rlock:
            try:
                for import_path, module_obj in modules:
                    assert import_path not in sys.modules
                    sys.modules[import_path] = module_obj
                yield
            finally:
                for import_path, _ in modules:
                    sys.modules.pop(import_path, None)


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


def import_module(dotted_path: str, module_obj) -> None:
    """
    Add module to sys.modules.

    :param dotted_path: the dotted path to be used in the imports.
    :param module_obj: the module object. It is assumed it has been already executed.
    :return: None
    """
    # if path is nested, and the root package is not present, add it to sys.modules
    split = dotted_path.split(".")
    if len(split) > 1 and split[0] not in sys.modules:
        root = split[0]
        sys.modules[root] = types.ModuleType(root)

    # add the module at the specified path.
    sys.modules[dotted_path] = module_obj


def load_agent_component_package(
    item_type: str, item_name: str, author_name: str, directory: os.PathLike
):
    """
    Load a Python package associated to a component..

    :param item_type: the type of the item. One of "protocol", "connection", "skill".
    :param item_name: the name of the item to load.
    :param author_name: the name of the author of the item to load.
    :param directory: the component directory.
    :return: the module associated to the Python package of the component.
    """
    item_type_plural = item_type + "s"
    dotted_path = "packages.{}.{}.{}".format(author_name, item_type_plural, item_name)
    filepath = Path(directory) / "__init__.py"
    return load_module(dotted_path, filepath)


def add_agent_component_module_to_sys_modules(
    item_type: str, item_name: str, author_name: str, module_obj
) -> None:
    """
    Add an agent component module to sys.modules.

    :param item_type: the type of the item. One of "protocol", "connection", "skill"
    :param item_name: the name of the item to load
    :param author_name: the name of the author of the item to load.
    :param module_obj: the module object. It is assumed it has been already executed.
    :return:
    """
    item_type_plural = item_type + "s"
    dotted_path = "packages.{}.{}.{}".format(author_name, item_type_plural, item_name)
    import_module(dotted_path, module_obj)
