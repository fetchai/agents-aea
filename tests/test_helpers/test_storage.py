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
"""This module contains the tests for aea helpers storage code."""
import asyncio
import os
import time

import pytest

from aea.helpers.storage import Storage


class TestAsyncCollection:
    """Test async storage collection."""

    @pytest.mark.asyncio
    async def test_collection(self):
        """Test collecton methods."""
        s = Storage("sqlite://:memory:")
        s.start()

        while not s.is_connected:
            await asyncio.sleep(0.01)

        col = await s.get_collection("test_col")
        col2 = await s.get_collection("another_collection")
        obj_id = "1"
        obj_body = {"a": 12}
        await col.put(obj_id, obj_body)
        assert await col.find("a", 12) == [obj_body]
        assert await col.get(obj_id) == obj_body
        assert await col2.get(obj_id) is None
        assert await col.get("not exists") is None

        await col.remove(obj_id)
        assert await col.get(obj_id) is None

        s.stop()
        await s.wait_completed()


class TestSyncCollection:
    """Test sync storage collection."""

    def test_collection(self):
        """Test collecton methods."""
        s = Storage("sqlite://:memory:", threaded=True)
        s.start()

        while not s.is_connected:
            time.sleep(0.01)

        obj_id = "1"
        obj_body = {"a": 12}

        col = s.get_sync_collection("test_col")
        col2 = s.get_sync_collection("another_collection")
        col.put(obj_id, obj_body)
        assert col.find("a", 12) == [obj_body]
        assert col.get(obj_id) == obj_body
        assert col2.get(obj_id) is None
        assert col.get("not exists") is None

        col.remove(obj_id)
        assert col.get(obj_id) is None

        s.stop()
        s.wait_completed(sync=True, timeout=5)


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
