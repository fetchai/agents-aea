# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This module contains the storage implementation."""
import asyncio
from typing import Any, Coroutine, List, Optional
from urllib.parse import urlparse

from aea.helpers.async_utils import AsyncState, Runnable
from aea.helpers.storage.backends.base import (
    AbstractStorageBackend,
    EQUALS_TYPE,
    JSON_TYPES,
    OBJECT_ID_AND_BODY,
)
from aea.helpers.storage.backends.sqlite import SqliteStorageBackend


BACKENDS = {"sqlite": SqliteStorageBackend}


class AsyncCollection:
    """Async collection."""

    def __init__(
        self, storage_backend: AbstractStorageBackend, collection_name: str
    ) -> None:
        """
        Init collection object.

        :param storage_backend: storage backed to use.
        :param collection_name: str
        """
        self._storage_backend = storage_backend
        self._collection_name = collection_name

    async def put(self, object_id: str, object_body: JSON_TYPES) -> None:
        """
        Put object into collection.

        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """

        return await self._storage_backend.put(
            self._collection_name, object_id, object_body
        )

    async def get(self, object_id: str) -> Optional[JSON_TYPES]:
        """
        Get object from the collection.

        :param object_id: str object id

        :return: dict if object exists in collection otherwise None
        """
        return await self._storage_backend.get(self._collection_name, object_id)

    async def remove(self, object_id: str) -> None:
        """
        Remove object from the collection.

        :param object_id: str object id

        :return: None
        """
        return await self._storage_backend.remove(self._collection_name, object_id)

    async def find(self, field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]:
        """
        Get objects from the collection by filtering by field value.

        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: None
        """
        return await self._storage_backend.find(self._collection_name, field, equals)

    async def list(self) -> List[OBJECT_ID_AND_BODY]:
        """
        List all objects with keys from the collection.

        :return: Tuple of objects keys, bodies.
        """
        return await self._storage_backend.list(self._collection_name)


class SyncCollection:
    """Async collection."""

    def __init__(
        self, async_collection_coro: Coroutine, loop: asyncio.AbstractEventLoop
    ) -> None:
        """
        Init collection object.

        :param async_collection_coro: coroutine returns async collection.
        :param loop: abstract event loop where storage is running.
        """
        self._loop = loop
        self._async_collection = self._run_sync(async_collection_coro)

    def _run_sync(self, coro: Coroutine) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def put(self, object_id: str, object_body: JSON_TYPES) -> None:
        """
        Put object into collection.

        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """
        return self._run_sync(self._async_collection.put(object_id, object_body))

    def get(self, object_id: str) -> Optional[JSON_TYPES]:
        """
        Get object from the collection.

        :param object_id: str object id

        :return: dict if object exists in collection otherwise None
        """
        return self._run_sync(self._async_collection.get(object_id))

    def remove(self, object_id: str) -> None:
        """
        Remove object from the collection.

        :param object_id: str object id

        :return: None
        """
        return self._run_sync(self._async_collection.remove(object_id))

    def find(self, field: str, equals: EQUALS_TYPE) -> List[OBJECT_ID_AND_BODY]:
        """
        Get objects from the collection by filtering by field value.

        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: List of object bodies
        """
        return self._run_sync(self._async_collection.find(field, equals))

    def list(self) -> List[OBJECT_ID_AND_BODY]:
        """
        List all objects with keys from the collection.

        :return: Tuple of objects keys, bodies.
        """
        return self._run_sync(self._async_collection.list())


class Storage(Runnable):
    """Generic storage."""

    def __init__(
        self,
        storage_uri: str,
        loop: asyncio.AbstractEventLoop = None,
        threaded: bool = False,
    ) -> None:
        """
        Init storage.

        :param storage_uri: configuration string for storage.
        :param loop: asyncio event loop to use.
        :param threaded: bool. start in thread if True.
        """
        super().__init__(loop=loop, threaded=threaded)
        self._storage_uri = storage_uri
        self._backend: AbstractStorageBackend = self._get_backend_instance(storage_uri)
        self._is_connected = False
        self._connected_state = AsyncState(False)

    async def wait_connected(self) -> None:
        """Wait generic storage is connected."""
        await self._connected_state.wait(True)

    @property
    def is_connected(self) -> bool:
        """Get running state of the storage."""
        return self._is_connected

    async def run(self) -> None:
        """Connect storage."""
        await self._backend.connect()
        self._is_connected = True
        self._connected_state.set(True)
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await self._backend.disconnect()
            self._is_connected = False

    @classmethod
    def _get_backend_instance(cls, uri: str) -> AbstractStorageBackend:
        """Construct backend instance."""
        backend_name = urlparse(uri).scheme
        backend_class = BACKENDS.get(backend_name, None)
        if backend_class is None:
            raise ValueError(
                f"Backend `{backend_name}` is not supported. Supported are {', '.join(BACKENDS.keys())} "
            )
        return backend_class(uri)

    async def get_collection(self, collection_name: str) -> AsyncCollection:
        """Get async collection."""
        await self._backend.ensure_collection(collection_name)
        return AsyncCollection(
            collection_name=collection_name, storage_backend=self._backend
        )

    def get_sync_collection(self, collection_name: str) -> SyncCollection:
        """Get sync collection."""
        if not self._loop:  # pragma: nocover
            raise ValueError("Storage not started!")
        return SyncCollection(self.get_collection(collection_name), self._loop)

    def __repr__(self) -> str:
        """Get string representation of the storage."""
        return f"[GenericStorage({self._storage_uri}){'Connected' if self.is_connected else 'Not connected'}]"
