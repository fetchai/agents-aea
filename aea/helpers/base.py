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
import re
import sys
import types
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Dict, Sequence, Tuple

from dotenv import load_dotenv

import yaml


logger = logging.getLogger(__name__)


def yaml_load(stream):
    def ordered_load(stream, object_pairs_hook=OrderedDict):
        class OrderedLoader(yaml.SafeLoader):
            pass

        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
        )
        return yaml.load(stream, OrderedLoader)  # nosec

    return ordered_load(stream)


def yaml_dump(data, stream):
    def ordered_dump(data, stream=None, **kwds):
        class OrderedDumper(yaml.SafeDumper):
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


def load_all_modules(
    directory: Path, glob: str = "*.py", prefix: str = ""
) -> Dict[str, types.ModuleType]:
    """
    Load all modules of a directory, recursively.

    :param directory: the directory where to search for .py modules.
    :param glob: the glob pattern to match. By default *.py
    :param prefix: the prefix to apply in the import path.
    :return: a mapping from import path to module objects.
    """
    if not directory.exists() or not directory.is_dir():
        raise ValueError("The provided path does not exists or it is not a directory.")
    result = {}  # type: Dict[str, types.ModuleType]
    package_root_directory = directory
    for module_path in directory.rglob(glob):
        relative_path_directory = module_path.relative_to(package_root_directory).parent
        # handle the case when relative_dotted_path is "."
        relative_dotted_path = (
            str(relative_path_directory).replace(os.path.sep, ".")
            if str(relative_path_directory) != "."
            else ""
        )
        if relative_dotted_path != "":
            prefix = prefix + "." + relative_dotted_path

        if module_path.name == "__init__.py":
            full_dotted_path = prefix
        else:
            full_dotted_path = ".".join([prefix, module_path.name[:-3]])

        module_obj = load_module(full_dotted_path, module_path)
        result[full_dotted_path] = module_obj
    return result


class _SysModules:
    """Helper class that load modules to sys.modules."""

    __rlock = RLock()

    @staticmethod
    @contextmanager
    def load_modules(modules: Sequence[Tuple[str, types.ModuleType]]):
        """
        Load modules as a context manager.

        :param modules: a list of pairs (import path, module object).
        :return: None.
        """
        with _SysModules.__rlock:
            # save the current state of sys.modules
            old_keys = set(sys.modules.keys())
            try:
                for import_path, module_obj in modules:
                    assert import_path not in sys.modules
                    sys.modules[import_path] = module_obj
                yield
            finally:
                pass
                # remove modules that:
                # - whose import path prefix is "packages." and
                # - were not loaded before us.
                keys = set(sys.modules.keys())
                for key in keys:
                    if re.match("^packages.?", key) and key not in old_keys:
                        sys.modules.pop(key, None)


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


def import_aea_module(dotted_path: str, module_obj) -> None:
    """
    Add an AEA module to sys.modules.

    The parameter dotted_path has the form:

        packages.<author_name>.<package_type>.<package_name>

    If the closed-prefix packages are not present, add them to sys.modules.
    This is done in order to emulate the behaviour of the true Python import system,
    which in fact imports the packages recursively, for every prefix.

    E.g. see https://docs.python.org/3/library/importlib.html#approximating-importlib-import-module
    for an explanation on how the 'import' built-in function works.

    :param dotted_path: the dotted path to be used in the imports.
    :param module_obj: the module object. It is assumed it has been already executed.
    :return: None
    """

    def add_namespace_to_sys_modules_if_not_present(dotted_path: str):
        if dotted_path not in sys.modules:
            sys.modules[dotted_path] = types.ModuleType(dotted_path)

    # add all prefixes as 'namespaces', since they are not actual packages.
    split = dotted_path.split(".")
    assert (
        len(split) > 3
    ), "Import path has not the form 'packages.<author_name>.<package_type>.<package_name>'"
    root = split[0]
    till_author = root + "." + split[1]
    till_item_type = till_author + "." + split[2]
    add_namespace_to_sys_modules_if_not_present(root)
    add_namespace_to_sys_modules_if_not_present(till_author)
    add_namespace_to_sys_modules_if_not_present(till_item_type)

    # finally, add the module at the specified path.
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


def add_modules_to_sys_modules(
    modules_by_import_path: Dict[str, types.ModuleType]
) -> None:
    """
    Load all modules in sys.modules.

    :param modules_by_import_path: a dictionary from import path to module objects.
    :return: None
    """
    for import_path, module_obj in modules_by_import_path.items():
        import_aea_module(import_path, module_obj)


def load_env_file(env_file: str):
    """
    Load the content of the environment file into the process environment.

    :param env_file: path to the env file.
    :return: None.
    """
    load_dotenv(dotenv_path=Path(env_file), override=False)
