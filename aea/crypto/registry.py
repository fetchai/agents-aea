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
"""
This module implements the crypto registry.
"""
import importlib
import re
from typing import Dict, Optional, Type, Union

from aea.crypto.base import Crypto
from aea.exceptions import AEAException
from aea.helpers.base import RegexConstrainedString

"""A regex to match a Python identifier (i.e. a module/class name)."""
PY_ID_REGEX = r"[^\d\W]\w*"


class CryptoId(RegexConstrainedString):
    """The identifier of a crypto class."""

    REGEX = re.compile(r"^({})$".format(PY_ID_REGEX))

    def __init__(self, seq):
        """Initialize the crypto id."""
        super().__init__(seq)

    @property
    def name(self):
        """Get the id name."""
        return self.data

    def _handle_no_match(self):
        raise AEAException(
            "Attempted to register malformed Crypto ID: {}. (Currently all IDs must be of the form {}.)".format(
                self.data, self.REGEX.pattern
            )
        )


class EntryPoint(RegexConstrainedString):
    """
    The entry point for a Crypto resource.

    The regular expression matches the strings in the following format:

        path.to.module:className
    """

    REGEX = re.compile(r"^({}(?:\.{})*):({})$".format(*[PY_ID_REGEX] * 3))

    def __init__(self, seq):
        """Initialize the entrypoint."""
        super().__init__(seq)

        match = self.REGEX.match(self.data)
        self._import_path = match.group(1)
        self._class_name = match.group(2)

    @property
    def import_path(self) -> str:
        """Get the import path."""
        return self._import_path

    @property
    def class_name(self) -> str:
        """Get the class name."""
        return self._class_name

    def _handle_no_match(self):
        raise AEAException(
            "Attempted to register malformed Crypto ID: {}. (Currently all IDs must be of the form {}.)".format(
                self.data, self.REGEX.pattern
            )
        )

    def load(self) -> Type[Crypto]:
        """
        Load the crypto object.

        :return: the cyrpto object, loaded following the spec.
        """
        mod_name, attr_name = self.import_path, self.class_name
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, attr_name)
        return fn


class CryptoSpec(object):
    """A specification for a particular instance of a crypto object."""

    def __init__(
        self, id: CryptoId, entry_point: EntryPoint, **kwargs: Dict,
    ):
        """
        Initialize a crypto specification.

        :param id: the id associated to this specification
        :param entry_point: The Python entry_point of the environment class (e.g. module.name:Class).
        :param kwargs: other custom keyword arguments.
        """
        self.id = CryptoId(id)
        self.entry_point = EntryPoint(entry_point)
        self._kwargs = {} if kwargs is None else kwargs

    def make(self, **kwargs) -> Crypto:
        """Instantiates an instance of the crypto object with appropriate arguments."""
        _kwargs = self._kwargs.copy()
        _kwargs.update(kwargs)
        cls = self.entry_point.load()
        crypto = cls()
        return crypto


class CryptoRegistry(object):
    """Registry for Crypto classes."""

    def __init__(self):
        """Initialize the Crypto registry."""
        self.specs = {}  # type: Dict[CryptoId, CryptoSpec]

    def register(self, id: CryptoId, entry_point: EntryPoint, **kwargs):
        """
        Register a Crypto module.

        :param id: the Cyrpto identifier (e.g. 'fetchai', 'ethereum' etc.)
        :param entry_point: the entry point, i.e. 'path.to.module:ClassName'
        :return: None
        """
        if id in self.specs:
            raise AEAException("Cannot re-register id: {}".format(id))
        self.specs[id] = CryptoSpec(id, entry_point, **kwargs)

    def make(self, id: CryptoId, module: Optional[str] = None, **kwargs) -> Crypto:
        """
        Make an instance of the crypto class associated to the given id.

        :param id: the id of the crypto class.
        :param module: see 'module' parameter to 'make'.
        :param kwargs: keyword arguments to be forwarded to the Crypto object.
        :return: the new Crypto instance.
        """
        spec = self._get_spec(id, module=module)
        crypto = spec.make(**kwargs)
        return crypto

    def _get_spec(self, id: CryptoId, module: Optional[str] = None):
        """Get the crypto spec."""
        if module is not None:
            try:
                importlib.import_module(module)
            except ImportError:
                raise AEAException(
                    "A module ({}) was specified for the environment but was not found, "
                    "make sure the package is installed with `pip install` before calling `aea.crypto.make()`".format(
                        module
                    )
                )

        if id not in self.specs:
            raise AEAException("Crypto not registered with id {}.".format(id))
        return self.specs[id]


registry = CryptoRegistry()


def register(
    id: Union[CryptoId, str], entry_point: Union[EntryPoint, str], **kwargs
) -> None:
    """
    Register a crypto type.

    :param id: the identifier for the crypto type.
    :param entry_point: the entry point to load the crypto object.
    :param kwargs: arguments to provide to the crypto class.
    :return: None.
    """
    crypto_id = CryptoId(id)
    entry_point = EntryPoint(entry_point)
    return registry.register(crypto_id, entry_point, **kwargs)


def make(id: Union[CryptoId, str], module: Optional[str] = None, **kwargs) -> Crypto:
    """
    Create a crypto instance.

    :param id: the id of the crypto object. Make sure it has been registered earlier
               before calling this function.
    :param module: dotted path to a module.
                   whether a module should be loaded before creating the object.
                   this argument is useful when the item might not be registered
                   beforehand, and loading the specified module will make the
                   registration.
                   E.g. suppose the call to 'register' for a custom crypto object
                   is located in some_package/__init__.py. By providing module="some_package",
                   the call to 'register' in such module gets triggered and
                   the make can then find the identifier.
    :param kwargs: keyword arguments to be forwarded to the Crypto object.
    :return:
    """
    crypto_id = CryptoId(id)
    return registry.make(crypto_id, module=module, **kwargs)
