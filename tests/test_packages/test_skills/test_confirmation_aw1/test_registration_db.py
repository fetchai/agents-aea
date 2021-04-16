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
"""This module contains the tests of the RegistrationDB class of the confirmation aw1 skill."""

from pathlib import Path
from unittest.mock import patch

import pytest

from aea.test_tools.test_skill import BaseSkillTestCase

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test RegistrationDB of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.custom_path = None
        cls.db = cls._skill.skill_context.registration_db
        cls.address = "some_address"

    def test__initialise_backend(self):
        """Test the _initialise_backend method of the RegistrationDB class."""
        # operation
        with patch("os.path.isfile", return_value=False) as mock_is_file:
            with patch.object(self.db, "_execute_single_sql") as mock_exe:
                self.db._initialise_backend()

        # after
        mock_is_file.assert_called_once()
        mock_exe.assert_any_call(
            "CREATE TABLE IF NOT EXISTS registered_table (address TEXT, ethereum_address TEXT, "
            "ethereum_signature TEXT, fetchai_signature TEXT, "
            "developer_handle TEXT, tweet TEXT)"
        )

    def test_set_registered(self):
        """Test the set_registered method of the RegistrationDB class."""
        # setup
        ethereum_address = "some_ethereum_address"
        ethereum_signature = "some_ethereum_signature"
        fetchai_signature = "some_fetchai_signature"
        developer_handle = "some_developer_handle"
        tweet = "some_tweet"

        # operation
        with patch.object(self.db, "_execute_single_sql") as mock_exe:
            self.db.set_registered(
                self.address,
                ethereum_address,
                ethereum_signature,
                fetchai_signature,
                developer_handle,
                tweet,
            )

        # after
        mock_exe.assert_any_call(
            "INSERT OR REPLACE INTO registered_table(address, ethereum_address, ethereum_signature, fetchai_signature, developer_handle, tweet) values(?, ?, ?, ?, ?, ?)",
            (
                self.address,
                ethereum_address,
                ethereum_signature,
                fetchai_signature,
                developer_handle,
                tweet,
            ),
        )

    def test_set_registered_developer_only(self):
        """Test the set_registered_developer_only method of the RegistrationDB class."""
        # setup
        developer_handle = "some_developer_handle"

        # operation
        with patch.object(self.db, "_execute_single_sql") as mock_exe:
            self.db.set_registered_developer_only(
                self.address, developer_handle,
            )

        # after
        mock_exe.assert_any_call(
            "INSERT OR REPLACE INTO registered_table(address, developer_handle) values(?, ?)",
            (self.address, developer_handle,),
        )

    def test_is_registered_i(self):
        """Test the is_registered method of the RegistrationDB class where result is NOT empty."""
        # setup
        result = [["1"], ["2", "3"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            is_registered = self.db.is_registered(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM registered_table WHERE address=?", (self.address,)
        )
        assert is_registered

    def test_is_registered_ii(self):
        """Test the is_registered method of the RegistrationDB class where result is empty."""
        # setup
        result = []

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            is_registered = self.db.is_registered(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT * FROM registered_table WHERE address=?", (self.address,)
        )
        assert not is_registered

    def test_get_developer_handle_i(self):
        """Test the get_developer_handle method of the RegistrationDB class where there is 1 developer handle in the result."""
        # setup
        developer_handle = "developer_handle_1"
        result = [[developer_handle], ["developer_handle_1"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_developer_handle = self.db.get_developer_handle(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT developer_handle FROM registered_table WHERE address=?",
            (self.address,),
        )
        assert actual_developer_handle == developer_handle

    def test_get_developer_handle_ii(self):
        """Test the get_developer_handle method of the RegistrationDB class where there is more than 1 developer handle in the result."""
        # setup
        developer_handle = "developer_handle_1"
        another_developer_handle = "developer_handle_2"
        result = [[developer_handle, another_developer_handle], ["developer_handle_1"]]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            with pytest.raises(
                ValueError,
                match=f"More than one developer_handle found for address={self.address}.",
            ):
                self.db.get_developer_handle(self.address)

        # after
        mock_exe.assert_any_call(
            "SELECT developer_handle FROM registered_table WHERE address=?",
            (self.address,),
        )

    def test_get_all_registered(self):
        """Test the get_all_registered method of the RegistrationDB class."""
        # setup
        result = [["1", "2", "3"], ["4", "5", "6"]]
        expected_registered = ["1", "4"]

        # operation
        with patch.object(
            self.db, "_execute_single_sql", return_value=result
        ) as mock_exe:
            actual_registered = self.db.get_all_registered()

        # after
        mock_exe.assert_any_call("SELECT address FROM registered_table", ())
        assert expected_registered == actual_registered
