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
"""This module contains the storage code."""
import asyncio
import json
import re
import sqlite3
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from aea.helpers.async_utils import Runnable


class AbstractStorageBackend(ABC):
    """Abstract base class for storage backend."""

    VALID_COL_NAME = re.compile("^[a-zA-Z0-9_]+$")

    def __init__(self, uri: str) -> None:
        """Init backend."""
        self._uri = uri

    def _check_collection_name(self, collection_name: str) -> None:
        """
        Check collection name is valid.

        raises ValueError if bad collection name provided.
        """
        if not self.VALID_COL_NAME.match(collection_name):
            raise ValueError(
                f"Invalid collection name: {collection_name}, should contains ony a-z and _"
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
        self, collection_name: str, object_id: str, object_body: Dict
    ) -> None:
        """
        Put object into collection.

        :param collection_name: str.
        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """

    @abstractmethod
    async def get(self, collection_name: str, object_id: str) -> Optional[Dict]:
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
    async def find(self, collection_name: str, field: str, equals: Any) -> List[Dict]:
        """
        Get objects from the collection by filtering by field value.

        :param collection_name: str.
        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: None
        """


class SqliteStorageBackend(AbstractStorageBackend):
    """Sqlite storage backend."""

    def __init__(self, uri: str) -> None:
        """Init backend."""
        super().__init__(uri)
        parsed = urlparse(uri)
        self._fname = parsed.netloc or parsed.path
        self._connection: Optional[sqlite3.Connection] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()

    def _execute_sql_sync(self, query: str, args: Optional[List] = None) -> List[Tuple]:
        """
        Execute sql command and return results.

        :param query: sql query string
        :param args: optional argumets to set into sql query.

        :return: List of tuples with sql records
        """
        if not self._connection:
            raise ValueError("Not connected")
        with self._lock:
            return self._connection.execute(query, args or []).fetchall()

    async def _executute_sql(self, query: str, args: Optional[List] = None):
        """
        Execute sql command and return results in async executor.

        :param query: sql query string
        :param args: optional argumets to set into sql query.

        :return: List of tuples with sql records
        """
        if not self._loop:
            raise ValueError("Not connected")
        return await self._loop.run_in_executor(
            None, self._execute_sql_sync, query, args
        )

    async def connect(self) -> None:
        """Connect to backend."""
        self._loop = asyncio.get_event_loop()
        self._connection = await self._loop.run_in_executor(
            None, sqlite3.connect, self._fname
        )

    async def disconnect(self) -> None:
        """Disconnect the backend."""
        if not self._loop or not self._connection:
            raise ValueError("Not connected")
        await self._loop.run_in_executor(None, self._connection.close)
        self._connection = None
        self._loop = None

    async def ensure_collection(self, collection_name: str) -> None:
        """
        Create collection if not exits.

        :param collection_name: str.
        :return: None
        """
        self._check_collection_name(collection_name)
        sql = f"""CREATE TABLE IF NOT EXISTS {collection_name} (
            object_id TEXT PRIMARY KEY,
            object_body JSON1 NOT NULL)
        """
        await self._executute_sql(sql)

    async def put(
        self, collection_name: str, object_id: str, object_body: Dict
    ) -> None:
        """
        Put object into collection.

        :param collection_name: str.
        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """
        self._check_collection_name(collection_name)
        sql = f"""INSERT INTO {collection_name} (object_id, object_body)
            VALUES (?, ?);
        """
        await self._executute_sql(sql, [object_id, json.dumps(object_body)])

    async def get(self, collection_name: str, object_id: str) -> Optional[Dict]:
        """
        Get object from the collection.

        :param collection_name: str.
        :param object_id: str object id

        :return: dict if object exists in collection otherwise None
        """
        self._check_collection_name(collection_name)
        sql = f"""SELECT object_body FROM {collection_name} WHERE object_id = ? LIMIT 1;"""
        result = await self._executute_sql(sql, [object_id])
        if result:
            return json.loads(result[0][0])
        return None

    async def remove(self, collection_name: str, object_id: str) -> None:
        """
        Remove object from the collection.

        :param collection_name: str.
        :param object_id: str object id

        :return: None
        """
        self._check_collection_name(collection_name)
        sql = f"""DELETE FROM {collection_name} WHERE object_id = ?;"""
        await self._executute_sql(sql, [object_id])

    async def find(self, collection_name: str, field: str, equals: Any) -> List[Dict]:
        """
        Get objects from the collection by filtering by field value.

        :param collection_name: str.
        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: None
        """
        self._check_collection_name(collection_name)
        sql = f"""SELECT object_body FROM {collection_name} WHERE json_extract(object_body, ?) = ?;"""
        if not field.startswith("$."):
            field = f"$.{field}"
        return [
            json.loads(i[0]) for i in await self._executute_sql(sql, [field, equals])
        ]


BACKENDS = {"sqlite": SqliteStorageBackend}


class AsyncCollection:
    """Async collection."""

    def __init__(self, storage_backend: AbstractStorageBackend, collection_name: str):
        """
        Init collection object.

        :param storage_backend: storage backed to use.
        :param collection_name: srt
        """
        self._storage_backend = storage_backend
        self._collection_name = collection_name

    async def put(self, object_id: str, object_body: Dict) -> None:
        """
        Put object into collection.

        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """

        return await self._storage_backend.put(
            self._collection_name, object_id, object_body
        )

    async def get(self, object_id: str) -> Optional[Dict]:
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

    async def find(self, field: str, equals: Any) -> List[Dict]:
        """
        Get objects from the collection by filtering by field value.

        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: None
        """
        return await self._storage_backend.find(self._collection_name, field, equals)


class SyncCollection:
    """Async collection."""

    def __init__(self, async_collection_coro, loop: asyncio.AbstractEventLoop):
        """
        Init collection object.

        :param async_collection_coro: coroutine returns async collection.
        :param loop: abstract event loop where storage is running.
        """
        self._loop = loop
        self._async_collection = self._run_sync(async_collection_coro)

    def _run_sync(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def put(self, object_id: str, object_body: Dict) -> None:
        """
        Put object into collection.

        :param object_id: str object id
        :param object_body: python dict, json compatible.
        :return: None
        """
        return self._run_sync(self._async_collection.put(object_id, object_body))

    def get(self, object_id: str) -> Optional[Dict]:
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

    def find(self, field: str, equals: Any) -> List[Dict]:
        """
        Get objects from the collection by filtering by field value.

        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to

        :return: None
        """
        return self._run_sync(self._async_collection.find(field, equals))


class Storage(Runnable):
    """Generic storage."""

    def __init__(
        self,
        storage_uri: str,
        loop: asyncio.AbstractEventLoop = None,
        threaded: bool = False,
    ) -> None:
        """
        Init stortage.

        :param storage_uri: configuration string for storage.
        :param loop: asyncio event loop to use.
        :param threaded: bool. start in thread if True.

        :return: None
        """
        super().__init__(loop=loop, threaded=threaded)
        self._storage_uri = storage_uri
        self._backend: AbstractStorageBackend = self._get_backend_instance(storage_uri)
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Get running state of the storage."""
        return self._is_connected

    async def run(self):
        """Connect storage."""
        await self._backend.connect()
        self._is_connected = True
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
        if not self._loop:
            raise ValueError("Storage not started!")
        return SyncCollection(self.get_collection(collection_name), self._loop)
