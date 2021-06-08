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

"""This module implements the base registry."""

import importlib
import re
from typing import Any, Dict, Generic, Optional, Set, Type, TypeVar, Union

from aea.configurations.base import PublicId
from aea.configurations.constants import DOTTED_PATH_MODULE_ELEMENT_SEPARATOR
from aea.exceptions import AEAException
from aea.helpers.base import RegexConstrainedString, SIMPLE_ID_REGEX


"""A regex to match a Python identifier (i.e. a module/class name)."""
PY_ID_REGEX = r"[^\d\W]\w*"
ITEM_ID_REGEX = fr"({SIMPLE_ID_REGEX})|{PublicId.PUBLIC_ID_REGEX}"
ItemType = TypeVar("ItemType")


def _handle_malformed_string(class_name: str, malformed_id: str) -> None:
    raise AEAException(
        "Malformed {}: '{}'. It must be of the form '{}'.".format(
            class_name, malformed_id, ItemId.REGEX.pattern
        )
    )


class ItemId(RegexConstrainedString):
    """The identifier of an item class."""

    REGEX = re.compile(r"^({})$".format(ITEM_ID_REGEX))

    @property
    def name(self) -> str:
        """Get the id name."""
        return self.data

    def _handle_no_match(self) -> None:
        _handle_malformed_string(ItemId.__name__, self.data)


class EntryPoint(Generic[ItemType], RegexConstrainedString):
    """
    The entry point for a resource.

    The regular expression matches the strings in the following format:

        path.to.module:className
    """

    REGEX = re.compile(
        r"^({pyid}(?:\.{pyid})*){sep}({pyid})$".format(
            pyid=PY_ID_REGEX, sep=DOTTED_PATH_MODULE_ELEMENT_SEPARATOR
        )
    )

    def __init__(self, seq: Union["EntryPoint", str]) -> None:
        """Initialize the entrypoint."""
        super().__init__(seq)

        match = self.REGEX.match(self.data)

        if match is None:
            # actual match done in base class
            raise ValueError("No match found!")  #  pragma: nocover

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

    def _handle_no_match(self) -> None:
        _handle_malformed_string(EntryPoint.__name__, self.data)

    def load(self) -> Type[ItemType]:
        """
        Load the item object.

        :return: the crypto object, loaded following the spec.
        """
        mod_name, attr_name = self.import_path, self.class_name
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, attr_name)
        return fn


class ItemSpec(Generic[ItemType]):
    """A specification for a particular instance of an object."""

    def __init__(
        self,
        id_: ItemId,
        entry_point: EntryPoint[ItemType],
        class_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Dict,
    ) -> None:
        """
        Initialize an item specification.

        :param id_: the id associated to this specification
        :param entry_point: The Python entry_point of the environment class (e.g. module.name:Class).
        :param class_kwargs: keyword arguments to be attached on the class as class variables.
        :param kwargs: other custom keyword arguments.
        """
        self.id = ItemId(id_)
        self.entry_point = EntryPoint[ItemType](entry_point)
        self._class_kwargs = {} if class_kwargs is None else class_kwargs
        self._kwargs = {} if kwargs is None else kwargs

    def make(self, **kwargs: Any) -> ItemType:
        """
        Instantiate an instance of the item object with appropriate arguments.

        :param kwargs: the key word arguments
        :return: an item
        """
        _kwargs = self._kwargs.copy()
        _kwargs.update(kwargs)
        cls = self.get_class()
        item = cls(**_kwargs)  # type: ignore
        return item

    def get_class(self) -> Type[ItemType]:
        """
        Get the class of the item with class variables instantiated.

        :return: an item class
        """
        cls = self.entry_point.load()
        for key, value in self._class_kwargs.items():
            setattr(cls, key, value)
        return cls


class Registry(Generic[ItemType]):
    """Registry for generic classes."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self.specs = {}  # type: Dict[ItemId, ItemSpec[ItemType]]

    @property
    def supported_ids(self) -> Set[str]:
        """Get the supported item ids."""
        return {str(id_) for id_ in self.specs.keys()}

    def register(
        self,
        id_: Union[ItemId, str],
        entry_point: Union[EntryPoint[ItemType], str],
        class_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Register an item type.

        :param id_: the identifier for the crypto type.
        :param entry_point: the entry point to load the crypto object.
        :param class_kwargs: keyword arguments to be attached on the class as class variables.
        :param kwargs: arguments to provide to the crypto class.
        """
        item_id = ItemId(id_)
        entry_point = EntryPoint[ItemType](entry_point)
        if item_id in self.specs:
            raise AEAException("Cannot re-register id: '{}'".format(item_id))
        self.specs[item_id] = ItemSpec[ItemType](
            item_id, entry_point, class_kwargs, **kwargs
        )

    def make(
        self, id_: Union[ItemId, str], module: Optional[str] = None, **kwargs: Any
    ) -> ItemType:
        """
        Create an instance of the associated type item id.

        :param id_: the id of the item class. Make sure it has been registered earlier
            before calling this function.
        :param module: dotted path to a module.
            whether a module should be loaded before creating the object.
            this argument is useful when the item might not be registered
            beforehand, and loading the specified module will make the registration.
            E.g. suppose the call to 'register' for a custom object
            is located in some_package/__init__.py. By providing module="some_package",
            the call to 'register' in such module gets triggered and
            the make can then find the identifier.
        :param kwargs: keyword arguments to be forwarded to the object.
        :return: the new item instance.
        """
        item_id = ItemId(id_)
        spec = self._get_spec(item_id, module=module)
        item = spec.make(**kwargs)
        return item

    def make_cls(
        self, id_: Union[ItemId, str], module: Optional[str] = None
    ) -> Type[ItemType]:
        """
        Load a class of the associated type item id.

        :param id_: the id of the item class. Make sure it has been registered earlier
            before calling this function.
        :param module: dotted path to a module.
            whether a module should be loaded before creating the object.
            this argument is useful when the item might not be registered
            beforehand, and loading the specified module will make the registration.
            E.g. suppose the call to 'register' for a custom object
            is located in some_package/__init__.py. By providing module="some_package",
            the call to 'register' in such module gets triggered and
            the make can then find the identifier.
        :return: the new item class.
        """
        item_id = ItemId(id_)
        spec = self._get_spec(item_id, module=module)
        cls = spec.get_class()
        return cls

    def has_spec(self, item_id: ItemId) -> bool:
        """
        Check whether there exist a spec associated with an item id.

        :param item_id: the item identifier.
        :return: True if it is registered, False otherwise.
        """
        return item_id in self.specs.keys()

    def _get_spec(
        self, item_id: ItemId, module: Optional[str] = None
    ) -> ItemSpec[ItemType]:
        """Get the item spec."""
        if module is not None:
            try:
                importlib.import_module(module)
            except ImportError:
                raise AEAException(
                    "A module ({}) was specified for the item but was not found, "
                    "make sure the package is installed with `pip install` before calling `aea.crypto.make()`".format(
                        module
                    )
                )

        if item_id not in self.specs:
            raise AEAException("Item not registered with id '{}'.".format(item_id))
        return self.specs[item_id]
