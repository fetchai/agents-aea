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
"""This module contains sqlite storage backend implementation."""
import asyncio
import json
import os
import platform
import sqlite3
import sys
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from aea.helpers.storage.backends.base import (
    AbstractStorageBackend,
    EQUALS_TYPE,
    JSON_TYPES,
    OBJECT_ID_AND_BODY,
)


class SqliteStorageBackend(AbstractStorageBackend):
    """Sqlite storage backend."""

    def __init__(self, uri: str) -> None:
        """Init backend."""
        super().__init__(uri)
        parsed = urlparse(self._uri)
        self._fname = parsed.netloc or parsed.path
        self._connection: Optional[sqlite3.Connection] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _execute_sql_sync(self, query: str, args: Optional[List] = None) -> List[Tuple]:
        """
        Execute sql command and return results.

        :param query: sql query string
        :param args: optional arguments to set into sql query.

        :return: List of tuples with sql records
        """
        if not self._connection:  # pragma: nocover
            raise ValueError("Not connected")
        with self._lock:
            result = self._connection.execute(query, args or []).fetchall()
            self._connection.commit()
            return result

    async def _executute_sql(
        self, query: str, args: Optional[List] = None
    ) -> Optional[JSON_TYPES]:
        """
        Execute sql command and return results in async executor.

        :param query: sql query string
        :param args: optional arguments to set into sql query.

        :return: List of tuples with sql records
        """
        if not self._loop:  # pragma: nocover
            raise ValueError("Not connected")
        return await self._loop.run_in_executor(
            self._executor, self._execute_sql_sync, query, args
        )

    async def connect(self) -> None:
        """Connect to backend."""
        self._loop = asyncio.get_event_loop()
        self._connection = await self._loop.run_in_executor(
            self._executor, self._do_connect, self._fname
        )

    @staticmethod
    def _do_connect(fname: str) -> sqlite3.Connection:
        con = sqlite3.connect(fname)
        if (
            platform.system() == "Windows"
            and sys.version_info.major == 3
            and sys.version_info.minor < 9
        ):  # pragma: nocover
            con.enable_load_extension(True)
            path_ext = Path(
                os.path.join(os.path.dirname(__file__), "binaries", "json1.dll")
            ).as_posix()
            con.load_extension(path_ext)
        return con

    async def disconnect(self) -> None:
        """Disconnect the backend."""
        if not self._loop or not self._connection:  # pragma: nocover
            raise ValueError("Not connected")
        await self._loop.run_in_executor(self._executor, self._connection.close)
        self._connection = None
        self._loop = None

    async def ensure_collection(self, collection_name: str) -> None:
        """
        Create collection if not exits.

        :param collection_name: name of the collection.
        """
        self._check_collection_name(collection_name)
        sql = f"""CREATE TABLE IF NOT EXISTS {collection_name} (
            object_id TEXT PRIMARY KEY,
            object_body JSON1 NOT NULL)
        """  # nosec
        await self._executute_sql(sql)

    async def put(
        self, collection_name: str, object_id: str, object_body: JSON_TYPES
    ) -> None:
        """
        Put object into collection.

        :param collection_name: str.
        :param object_id: str object id
        :param object_body: python dict, json compatible.
        """
        self._check_collection_name(collection_name)
        sql = f"""INSERT OR REPLACE INTO {collection_name} (object_id, object_body)
            VALUES (?, ?);
        """  # nosec
        await self._executute_sql(sql, [object_id, json.dumps(object_body)])

    async def get(self, collection_name: str, object_id: str) -> Optional[JSON_TYPES]:
        """
        Get object from the collection.

        :param collection_name: str.
        :param object_id: str object id

        :return: dict if object exists in collection otherwise None
        """
        self._check_collection_name(collection_name)
        sql = f"""SELECT object_body FROM {collection_name} WHERE object_id = ? LIMIT 1;"""  # nosec
        result = await self._executute_sql(sql, [object_id])
        if (
            result
            and isinstance(result, (list, tuple))
            and len(result) > 0
            and isinstance(result[0], (list, tuple))
            and len(result[0]) > 0
        ):
            return json.loads(result[0][0])
        return None

    async def remove(self, collection_name: str, object_id: str) -> None:
        """
        Remove object from the collection.

        :param collection_name: str.
        :param object_id: str object id
        """
        self._check_collection_name(collection_name)
        sql = f"""DELETE FROM {collection_name} WHERE object_id = ?;"""  # nosec
        await self._executute_sql(sql, [object_id])

    async def find(
        self, collection_name: str, field: str, equals: EQUALS_TYPE
    ) -> List[OBJECT_ID_AND_BODY]:
        """
        Get objects from the collection by filtering by field value.

        :param collection_name: str.
        :param field: field name to search: example "parent.field"
        :param equals: value field should be equal to
        :return: list of object ids and body
        """
        self._check_collection_name(collection_name)
        sql = f"""SELECT object_id, object_body FROM {collection_name} WHERE json_extract(object_body, ?) = ?;"""  # nosec
        if not field.startswith("$."):
            field = f"$.{field}"
        return [
            (i[0], json.loads(i[1]))
            for i in await self._executute_sql(sql, [field, equals])  # type: ignore
        ]

    async def list(self, collection_name: str) -> List[OBJECT_ID_AND_BODY]:
        """
        List all objects with keys from the collection.

        :param collection_name: str.
        :return: Tuple of objects keys, bodies.
        """
        self._check_collection_name(collection_name)
        sql = f"""SELECT object_id, object_body FROM {collection_name};"""  # nosec
        return [(i[0], json.loads(i[1])) for i in await self._executute_sql(sql)]  # type: ignore
