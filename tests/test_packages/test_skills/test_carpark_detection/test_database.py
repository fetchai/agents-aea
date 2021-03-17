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
"""This module contains the tests of the RegistrationDB class of the carpark detection skill."""
import os
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.carpark_detection.database import DetectionDatabase

from tests.conftest import ROOT_DIR


class TestDetectionDatabase(BaseSkillTestCase):
    """Test DetectionDatabase of carpark detection."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "carpark_detection")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.temp_dir = os.path.join(os.path.dirname(__file__), "temp_files_placeholder")
        cls.create_if_not_present = True
        cls.logger = None
        cls.db = DetectionDatabase(
            temp_dir=cls.temp_dir,
            create_if_not_present=cls.create_if_not_present,
            logger=cls.logger,
        )

    def test__init__i(self):
        """Test the __init__ method of the DetectionDatabase class."""
        # operation
        with patch.object(self.db, "initialise_backend") as mock_initialise_back:
            self.db.__init__(self.temp_dir, self.create_if_not_present, self.logger)

        mock_initialise_back.assert_called_once()

    def test_is_db_exits_i(self):
        """Test the is_db_exits method of the DetectionDatabase class where db exists."""
        # operation
        with patch("os.path.isfile", return_value=True) as mock_is_file:
            with patch.object(
                self.db, "get_system_status", return_value="Exists"
            ) as mock_status:
                exists = self.db.is_db_exits()

        # after
        mock_is_file.assert_any_call(self.db.database_path)
        mock_status.assert_any_call("db", False)

        assert exists is True

    def test_is_db_exits_ii(self):
        """Test the is_db_exits method of the DetectionDatabase class where db file does NOT exist."""
        # operation
        with patch("os.path.isfile", return_value=False) as mock_is_file:
            exists = self.db.is_db_exits()

        # after
        mock_is_file.assert_any_call(self.db.database_path)
        assert exists is False

    def test_is_db_exits_iii(self):
        """Test the is_db_exits method of the DetectionDatabase class where db status does NOT contain Exists."""
        # operation
        with patch("os.path.isfile", return_value=True) as mock_is_file:
            with patch.object(
                self.db, "get_system_status", return_value="Something"
            ) as mock_status:
                exists = self.db.is_db_exits()

        # after
        mock_is_file.assert_any_call(self.db.database_path)
        mock_status.assert_any_call("db", False)

        assert exists is False

    def test_initialise_backend_i(self):
        """Test the initialise_backend method of the DetectionDatabase class where db NOT exists."""
        # operation
        with patch.object(self.db, "ensure_dirs_exist") as mock_ensure:
            with patch.object(self.db, "execute_single_sql") as mock_sql:
                with patch.object(
                    self.db, "is_db_exits", return_value=False
                ) as mock_exists:
                    with patch.object(self.db, "set_system_status") as mock_status:
                        self.db.initialise_backend()

        # after
        mock_ensure.assert_called_once()
        mock_sql.assert_called()
        assert mock_sql.call_count == 6
        mock_exists.assert_called_once()
        mock_status.assert_called()
        assert mock_status.call_count == 3

    def test_initialise_backend_ii(self):
        """Test the initialise_backend method of the DetectionDatabase class where db exists."""
        # operation
        with patch.object(self.db, "ensure_dirs_exist") as mock_ensure:
            with patch.object(self.db, "execute_single_sql") as mock_sql:
                with patch.object(
                    self.db, "is_db_exits", return_value=True
                ) as mock_exists:
                    with patch.object(self.db, "set_system_status") as mock_status:
                        self.db.initialise_backend()

        # after
        mock_ensure.assert_called_once()
        mock_sql.assert_called()
        assert mock_sql.call_count == 6
        mock_exists.assert_called_once()
        mock_status.assert_called()
        assert mock_status.call_count == 1

    def test_get_lat_lon_i(self):
        """Test the get_lat_lon method of the DetectionDatabase class where lat and lon are UNKNOWN."""
        # setup
        lat = 1.2
        lon = 3
        expected_lon = 3.0

        # operation
        with patch.object(
            self.db, "get_system_status", side_effect=[lat, lon]
        ) as mock_status:
            actual_lat, actual_lon = self.db.get_lat_lon()

        # after
        mock_status.assert_called()
        assert mock_status.call_count == 2
        assert actual_lat == lat
        assert actual_lon == expected_lon

    def test_get_lat_lon_ii(self):
        """Test the get_lat_lon method of the DetectionDatabase class where lat and lon are NOT UNKNOWN."""
        # setup
        lat = "UNKNOWN"
        lon = "UNKNOWN"

        # operation
        with patch.object(
            self.db, "get_system_status", side_effect=[lat, lon]
        ) as mock_status:
            actual_lat, actual_lon = self.db.get_lat_lon()

        # after
        mock_status.assert_called()
        assert mock_status.call_count == 2
        assert actual_lat is None
        assert actual_lon is None

    def test_set_system_status(self):
        """Test the set_system_status method of the DetectionDatabase class."""
        # setup
        system_name = "some_system_name"
        status = "some_status"

        # operation
        with patch.object(self.db, "execute_single_sql") as mock_sql:
            self.db.set_system_status(system_name, status)

        # after
        mock_sql.assert_any_call(
            "INSERT OR REPLACE INTO status_table(system_name, status) values(?, ?)",
            (system_name, status),
        )

    def test_get_system_status_i(self):
        """Test the get_system_status method of the DetectionDatabase class where result is NOT empty."""
        # setup
        system_name = "some_system_name"
        print_exceptions = True

        expected_result = 1
        mocked_result = [[expected_result, 2], [3, 4]]

        # operation
        with patch.object(
            self.db, "execute_single_sql", return_value=mocked_result
        ) as mock_sql:
            actual_result = self.db.get_system_status(system_name, print_exceptions)

        # after
        mock_sql.assert_any_call(
            "SELECT status FROM status_table WHERE system_name=?",
            (system_name,),
            print_exceptions,
        )
        assert actual_result == expected_result

    def test_get_system_status_ii(self):
        """Test the get_system_status method of the DetectionDatabase class where result IS empty."""
        # setup
        system_name = "some_system_name"
        print_exceptions = True

        mocked_result = []

        # operation
        with patch.object(
            self.db, "execute_single_sql", return_value=mocked_result
        ) as mock_sql:
            actual_result = self.db.get_system_status(system_name, print_exceptions)

        # after
        mock_sql.assert_any_call(
            "SELECT status FROM status_table WHERE system_name=?",
            (system_name,),
            print_exceptions,
        )
        assert actual_result == "UNKNOWN"

    def test_execute_single_sql_i(self):
        """Test the execute_single_sql method of the DBCommunication class where NO exception is thrown."""
        # setup
        command = "some_command"
        variables = (1, "2", 4.3)
        print_exceptions = True
        result = [1, 2, 3, 4, 5]

        mocked_conn = Mock(wrap=sqlite3.Connection)
        mocked_cursor = Mock(wraps=sqlite3.Cursor)

        # operation

        with patch("sqlite3.connect", return_value=mocked_conn) as mock_conn:
            with patch.object(
                mocked_conn, "cursor", return_value=mocked_cursor
            ) as mock_curs:
                with patch.object(mocked_cursor, "execute") as mock_exe:
                    with patch.object(
                        mocked_cursor, "fetchall", return_value=result
                    ) as mock_fetchall:
                        with patch.object(mocked_conn, "commit") as mock_commit:
                            with patch.object(mocked_conn, "close") as mock_con_close:
                                actual_result = self.db.execute_single_sql(
                                    command, variables, print_exceptions
                                )

        # after
        mock_conn.assert_called_once()
        mock_curs.assert_called_once()
        mock_exe.assert_any_call(
            command, variables,
        )
        mock_fetchall.assert_called_once()
        mock_commit.assert_called_once()
        mock_con_close.assert_called_once()
        assert actual_result == result

    def test_execute_single_sql_ii(self):
        """Test the execute_single_sql method of the DBCommunication class where an exception IS thrown."""
        # setup
        command = "some_command"
        variables = (1, "2", 4.3)
        print_exceptions = True
        result = [1, 2, 3, 4, 5]
        exception_message = "some_exception_message"

        mocked_conn = Mock(wrap=sqlite3.Connection)
        mocked_cursor = Mock(wraps=sqlite3.Cursor)

        # operation

        with patch("sqlite3.connect", return_value=mocked_conn) as mock_conn:
            with patch.object(
                mocked_conn, "cursor", return_value=mocked_cursor
            ) as mock_curs:
                with patch.object(mocked_cursor, "execute") as mock_exe:
                    with patch.object(
                        mocked_cursor, "fetchall", return_value=result
                    ) as mock_fetchall:
                        with patch.object(
                            mocked_conn,
                            "commit",
                            side_effect=ValueError(exception_message),
                        ) as mock_commit:
                            with patch.object(mocked_conn, "close") as mock_con_close:
                                with patch.object(
                                    self.db.logger, "warning"
                                ) as mock_logger:
                                    actual_result = self.db.execute_single_sql(
                                        command, variables, print_exceptions
                                    )

        # after
        mock_conn.assert_called_once()
        mock_curs.assert_called_once()
        mock_exe.assert_any_call(
            command, variables,
        )
        mock_fetchall.assert_called_once()
        mock_commit.assert_called_once()
        mock_logger.assert_any_call(f"Exception in database: {exception_message}",)
        mock_con_close.assert_called_once()
        assert actual_result == result

    def test_get_latest_detection_data_i(self):
        """Test the get_latest_detection_data method of the DBCommunication class where result is NOT None."""
        # setup
        max_num_rows = 2
        command = """SELECT * FROM images ORDER BY epoch DESC LIMIT ?"""
        result = [[1, 2, 3, 4, 5, 6, 7, 8]]
        expected_result = [
            {
                "epoch": result[0][0],
                "raw_image_path": result[0][1],
                "processed_image_path": result[0][2],
                "total_count": result[0][3],
                "moving_count": result[0][4],
                "free_spaces": result[0][5],
                "lat": result[0][6],
                "lon": result[0][7],
            }
        ]

        # operation
        with patch.object(
            self.db, "execute_single_sql", return_value=result
        ) as mock_exe:
            actual_result = self.db.get_latest_detection_data(max_num_rows)

        # after
        mock_exe.assert_any_call(
            command, (max_num_rows,),
        )
        assert actual_result == expected_result

    def test_get_latest_detection_data_ii(self):
        """Test the get_latest_detection_data method of the DBCommunication class where result IS None."""
        # setup
        max_num_rows = 2
        command = """SELECT * FROM images ORDER BY epoch DESC LIMIT ?"""
        result = None

        # operation
        with patch.object(
            self.db, "execute_single_sql", return_value=result
        ) as mock_exe:
            actual_result = self.db.get_latest_detection_data(max_num_rows)

        # after
        mock_exe.assert_any_call(
            command, (max_num_rows,),
        )
        assert actual_result is None

    def test_ensure_dirs_exist(self):
        """Test the ensure_dirs_exist method of the DetectionDatabase class where db exists."""
        # operation
        with patch("os.path.isdir", return_value=False) as mock_is_dir:
            with patch("os.mkdir") as mock_mkdir:
                self.db.ensure_dirs_exist()

        # after
        mock_is_dir.assert_any_call(self.db.temp_dir)
        mock_is_dir.assert_any_call(self.db.raw_image_dir)
        mock_is_dir.assert_any_call(self.db.processed_image_dir)

        mock_mkdir.assert_any_call(self.db.temp_dir)
        mock_mkdir.assert_any_call(self.db.raw_image_dir)
        mock_mkdir.assert_any_call(self.db.processed_image_dir)
