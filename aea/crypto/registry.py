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

"""This module implements the crypto registry."""

import importlib
import re
from typing import Dict, Optional, Set, Type, Union

from aea.crypto.base import Crypto
from aea.exceptions import AEAException
from aea.helpers.base import RegexConstrainedString

"""A regex to match a Python identifier (i.e. a module/class name)."""
PY_ID_REGEX = r"[^\d\W]\w*"


def _handle_malformed_string(class_name: str, malformed_id: str):
    raise AEAException(
        "Malformed {}: '{}'. It must be of the form '{}'.".format(
            class_name, malformed_id, CryptoId.REGEX.pattern
        )
    )


class CryptoId(RegexConstrainedString):
    """The identifier of a crypto class."""

    REGEX = re.compile(r"^({})$".format(PY_ID_REGEX))

    def __init__(self, seq):  # pylint: disable=useless-super-delegation
        """Initialize the crypto id."""
        super().__init__(seq)

    @property
    def name(self):
        """Get the id name."""
        return self.data

    def _handle_no_match(self):
        _handle_malformed_string(CryptoId.__name__, self.data)


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
        _handle_malformed_string(EntryPoint.__name__, self.data)

    def load(self) -> Type[Crypto]:
        """
        Load the crypto object.

        :return: the cyrpto object, loaded following the spec.
        """
        mod_name, attr_name = self.import_path, self.class_name
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, attr_name)
        return fn


class CryptoSpec:
    """A specification for a particular instance of a crypto object."""

    def __init__(
        self, crypto_id: CryptoId, entry_point: EntryPoint, **kwargs: Dict,
    ):
        """
        Initialize a crypto specification.

        :param id: the id associated to this specification
        :param entry_point: The Python entry_point of the environment class (e.g. module.name:Class).
        :param kwargs: other custom keyword arguments.
        """
        self.id = CryptoId(crypto_id)
        self.entry_point = EntryPoint(entry_point)
        self._kwargs = {} if kwargs is None else kwargs

    def make(self, **kwargs) -> Crypto:
        """
        Instantiate an instance of the crypto object with appropriate arguments.

        :param kwargs: the key word arguments
        :return: a crypto object
        """
        _kwargs = self._kwargs.copy()
        _kwargs.update(kwargs)
        cls = self.entry_point.load()
        crypto = cls(**kwargs)
        return crypto


class CryptoRegistry:
    """Registry for Crypto classes."""

    def __init__(self):
        """Initialize the Crypto registry."""
        self.specs = {}  # type: Dict[CryptoId, CryptoSpec]

    @property
    def supported_crypto_ids(self) -> Set[str]:
        """Get the supported crypto ids."""
        return set([str(id_) for id_ in self.specs.keys()])

    def register(self, crypto_id: CryptoId, entry_point: EntryPoint, **kwargs):
        """
        Register a Crypto module.

        :param crypto_id: the Cyrpto identifier (e.g. 'fetchai', 'ethereum' etc.)
        :param entry_point: the entry point, i.e. 'path.to.module:ClassName'
        :return: None
        """
        if crypto_id in self.specs:
            raise AEAException("Cannot re-register id: '{}'".format(crypto_id))
        self.specs[crypto_id] = CryptoSpec(crypto_id, entry_point, **kwargs)

    def make(self, crypto_id: CryptoId, module: Optional[str] = None, **kwargs) -> Crypto:
        """
        Make an instance of the crypto class associated to the given id.

        :param crypto_id: the id of the crypto class.
        :param module: see 'module' parameter to 'make'.
        :param kwargs: keyword arguments to be forwarded to the Crypto object.
        :return: the new Crypto instance.
        """
        spec = self._get_spec(crypto_id, module=module)
        crypto = spec.make(**kwargs)
        return crypto

    def has_spec(self, crypto_id: CryptoId) -> bool:
        """
        Check whether there exist a spec associated with a crypto id.

        :param crypto_id: the crypto identifier.
        :return: True if it is registered, False otherwise.
        """
        return crypto_id in self.specs.keys()

    def _get_spec(self, crypto_id: CryptoId, module: Optional[str] = None):
        """Get the crypto spec."""
        if module is not None:
            try:
                importlib.import_module(module)
            except ImportError:
                raise AEAException(
                    "A module ({}) was specified for the crypto but was not found, "
                    "make sure the package is installed with `pip install` before calling `aea.crypto.make()`".format(
                        module
                    )
                )

        if crypto_id not in self.specs:
            raise AEAException("Crypto not registered with id '{}'.".format(crypto_id))
        return self.specs[crypto_id]


registry = CryptoRegistry()


def register(
    crypto_id: Union[CryptoId, str], entry_point: Union[EntryPoint, str], **kwargs
) -> None:
    """
    Register a crypto type.

    :param crypto_id: the identifier for the crypto type.
    :param entry_point: the entry point to load the crypto object.
    :param kwargs: arguments to provide to the crypto class.
    :return: None.
    """
    crypto_id = CryptoId(crypto_id)
    entry_point = EntryPoint(entry_point)
    return registry.register(crypto_id, entry_point, **kwargs)


def make(crypto_id: Union[CryptoId, str], module: Optional[str] = None, **kwargs) -> Crypto:
    """
    Create a crypto instance.

    :param crypto_id: the id of the crypto object. Make sure it has been registered earlier
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
    crypto_id = CryptoId(crypto_id)
    return registry.make(crypto_id, module=module, **kwargs)
