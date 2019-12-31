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
import sys
from pathlib import Path
from typing import Optional

import importlib.util
import logging
import os

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
    parts = [part for part in path.split('.') if part]
    module, n = None, 0
    while n < len(parts):
        file_location = os.path.join(*parts[:n + 1])
        spec_name = '.'.join(parts[:n + 1])
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


def load_module(name: str, filepath: os.PathLike):
    """
    Load a module.

    :param name: the name of the package/module.
    :param filepath: the file to the package/module.
    :return: None
    :raises ValueError: if the filepath provided is not a module.
    :raises Exception: if the execution of the module raises exception.
    """
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def add_agent_component_module_to_sys_modules(item_type: str, item_name: str, module_obj):
    item_type_plural = item_type + "s"
    dotted_path = "packages.{}.{}".format(item_type_plural, item_name)
    sys.modules[dotted_path] = module_obj


def generate_fingerprint(author: str, package_name: str, version: str, nonce: Optional[int] = None) -> str:
    """Generate a unique id for the package.

    :param author: The author of the package.
    :param package_name: The name of the package
    :param version: The version of the package.
    :param nonce: Enable the developer to generate two different fingerprints for the same package.
           (Can be used with different configuration)
    """
    import hashlib
    if nonce is not None:
        string_for_hash = "".join([author, package_name, version, str(nonce)])
    else:
        string_for_hash = "".join([author, package_name, version])
    m_hash = hashlib.sha3_256()
    m_hash.update(string_for_hash.encode())
    encoded_str = m_hash.digest().hex()
    return encoded_str
