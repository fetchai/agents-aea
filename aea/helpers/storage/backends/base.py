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
"""This module contains storage abstract backend class."""
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

from aea.helpers.constants import JSON_TYPES


EQUALS_TYPE = Union[int, float, str, bool]
OBJECT_ID_AND_BODY = Tuple[str, JSON_TYPES]


class AbstractStorageBackend(ABC):
    """Abstract base class for storage backend."""

    VALID_COL_NAME = re.compile("^[a-zA-Z0-9_]+$")

    def __init__(self, uri: str) -> None:
        """Init backend."""
        self._uri = uri

    def _check_collection_name(self, collection_name: str) -> None:
        """
        Check collection name is valid.

        :param collection_name: the collection name.
        :raises ValueError: if bad collection name provided.
        """
        if not self.VALID_COL_NAME.match(collection_name):
            raise ValueError(
                f"Invalid collection name: {collection_name}, should contain only alpha-numeric characters and _"
            )

    @abstractmethod
    async def connect(self) -> None:
        """Connect to backend."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect the backend."""

    @abstractmethod
    async def ensure_collection(self, collection_name: str) -> None:
        """
        Create collection if not exits.

        :param collection_name: str.
        :return: None
        """

    @abstractmethod
    async def put(
        self, collection_name: str, object_id: str, object_body: JSON_TYPES
    ) -> None:
        """
        Put object into collection.

        :param collection_name: str.
        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """

    @abstractmethod
    async def get(self, collection_name: str, object_id: str) -> Optional[JSON_TYPES]:
        """
        Get object from the collection.

        :param collection_name: str.
        :param object_id: str object id

        :return: dict if object exists in collection otherwise None
        """

    @abstractmethod
    async def remove(self, collection_name: str, object_id: str) -> None:
        """
        Remove object from the collection.

        :param collection_name: str.
        :param object_id: str object id

        :return: None
        """

    @abstractmethod
    async def find(
        self, collection_name: str, field: str, equals: EQUALS_TYPE
    ) -> List[OBJECT_ID_AND_BODY]:
        """
        Get objects from the collection by filtering by field value.

        :param collection_name: str.
        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return:  list of objects bodies
        """

    @abstractmethod
    async def list(self, collection_name: str) -> List[OBJECT_ID_AND_BODY]:
        """
        List all objects with keys from the collection.

        :param collection_name: str.
        :return: Tuple of objects keys, bodies.
        """
