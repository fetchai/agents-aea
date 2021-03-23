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
"""Communicate between the database and the python objects."""

import logging
import os
import shutil
import sqlite3
import time
from typing import Dict, List, Optional, Tuple, Union

import skimage  # type: ignore


_default_logger = logging.getLogger(
    "aea.packages.fetchai.skills.carpark_detection.detection_database"
)


class DetectionDatabase:  # pylint: disable=too-many-public-methods
    """Communicate between the database and the python objects."""

    def __init__(
        self,
        temp_dir: str,
        create_if_not_present: bool = True,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialise the Detection Database Communication class."""
        self.this_dir = os.path.dirname(__file__)
        self.temp_dir = temp_dir

        self.mask_image_path = self.temp_dir + "/mask.tiff"
        self.mask_ref_image_path = self.temp_dir + "/mask_ref.tiff"
        self.raw_image_dir = self.temp_dir + "/db_raw_images/"
        self.processed_image_dir = self.temp_dir + "/db_processed_images/"
        # Note that this path should be under source control
        self.default_mask_ref_path = self.this_dir + "/default_mask_ref.png"
        self.num_digits_time = (
            12  # need to match this up with the generate functions below
        )
        self.image_file_ext = ".png"
        self.database_path = self.temp_dir + "/" + "detection_results.db"

        if create_if_not_present:
            self.initialise_backend()

        self.logger = logger if logger is not None else _default_logger

    def is_db_exits(self) -> bool:
        """Return true if database exists and is set up."""
        if not os.path.isfile(self.database_path):
            return False

        ret = self.get_system_status("db", False) == "Exists"
        return ret

    def reset_database(self) -> None:  # pragma: nocover
        """Reset the database and remove all data."""
        # If we need to reset the database, then remove the table and any stored images
        self.logger.info("Database being reset.")

        # Remove the actual database file
        if os.path.isfile(self.database_path):
            os.remove(self.database_path)

        # Clear stored images
        shutil.rmtree(self.raw_image_dir)
        shutil.rmtree(self.processed_image_dir)

        # Recreate them
        self.logger.info("Initialising backend ...")
        self.initialise_backend()
        self.logger.info("Finished initialising backend!")

    def reset_mask(self) -> None:  # pragma: nocover
        """Just reset the detection mask."""
        # If we need to reset the database, then remove the table and any stored images
        self.logger.info("Mask being reset.")

        # Remove the actual database file
        if os.path.isfile(self.mask_image_path):
            os.remove(self.mask_image_path)
        if os.path.isfile(self.mask_ref_image_path):
            os.remove(self.mask_ref_image_path)
        self.ensure_dirs_exist()

    def initialise_backend(self) -> None:
        """Set up database and initialise the tables."""
        self.ensure_dirs_exist()
        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS images (epoch INTEGER, raw_image_path TEXT, "
            "processed_image_path TEXT, total_count INTEGER, "
            "moving_count INTEGER, free_spaces INTEGER, lat TEXT, lon TEXT)"
        )

        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS fet_table (id INTEGER PRIMARY KEY, amount BIGINT, last_updated TEXT)"
        )

        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS status_table (system_name TEXT PRIMARY KEY, status TEXT)"
        )

        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS name_lookup2 (oef_key TEXT PRIMARY KEY, friendly_name TEXT, epoch INT, is_self BIT)"
        )

        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS transaction_history (tx TEXT PRIMARY KEY, epoch INT, oef_key_payer TEXT, oef_key_payee TEXT, amount BIGINT, status TEXT)"
        )

        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS dialogue_statuses (dialogue_id TEXT, epoch DECIMAL, other_agent_key TEXT, received_msg TEXT, sent_msg TEXT)"
        )

        if not self.is_db_exits():
            self.set_system_status("lat", "UNKNOWN")
            self.set_system_status("lon", "UNKNOWN")
        self.set_system_status("db", "Exists")

    def set_fet(self, amount: int, t: str) -> None:  # pragma: nocover
        """Record how much FET we have and when we last read it from the ledger."""
        command = (
            "INSERT OR REPLACE INTO fet_table(id, amount, last_updated) values(0, ?, ?)"
        )
        variables = (str(amount), str(t))
        self.execute_single_sql(command, variables)

    def get_fet(self) -> int:  # pragma: nocover
        """Read how much FET we have."""
        result = self.execute_single_sql("SELECT amount FROM fet_table WHERE id=0")
        if len(result) != 0:
            return result[0][0]
        return -99

    def save_max_capacity(self, max_capacity: int) -> None:  # pragma: nocover
        """Record the maximum number of spaces we can report on."""
        self.set_system_status("max_capacity", str(max_capacity))

    def get_max_capacity(self) -> Optional[int]:  # pragma: nocover
        """Read the maximum number of spaces we can report on."""
        max_capacity = self.get_system_status("max_capacity")

        if max_capacity == "UNKNOWN":
            return None
        return int(max_capacity)

    def save_lat_lon(self, lat: float, lon: float) -> None:  # pragma: nocover
        """Record the longitude and latitude of our device."""
        self.set_system_status("lat", str(lat))
        self.set_system_status("lon", str(lon))

    def get_lat_lon(self) -> Tuple[Optional[float], Optional[float]]:
        """Read the longitude and latitude of our device."""
        lat = self.get_system_status("lat")
        lon = self.get_system_status("lon")
        if lat == "UNKNOWN" or lon == "UNKNOWN":
            return None, None
        return float(lat), float(lon)

    def set_system_status(self, system_name: str, status: str) -> None:
        """Record the status of one of the systems."""
        command = (
            "INSERT OR REPLACE INTO status_table(system_name, status) values(?, ?)"
        )
        variables = (str(system_name), str(status))
        self.execute_single_sql(command, variables)

    def get_system_status(self, system_name: str, print_exceptions: bool = True) -> str:
        """Read the status of one of the systems."""
        command = "SELECT status FROM status_table WHERE system_name=?"
        variables = (str(system_name),)
        result = self.execute_single_sql(command, variables, print_exceptions)
        if len(result) != 0:
            return result[0][0]
        return "UNKNOWN"

    def set_dialogue_status(
        self, dialogue_id: int, other_agent_key: str, received_msg: str, sent_msg: str
    ) -> None:  # pragma: nocover
        """Record the status of a dialog we are having."""
        t = time.time()
        command = "INSERT INTO dialogue_statuses(dialogue_id, epoch, other_agent_key, received_msg, sent_msg) VALUES(?,?,?,?,?)"
        variables = (
            str(dialogue_id),
            str(t),
            str(other_agent_key),
            str(received_msg),
            str(sent_msg),
        )
        self.execute_single_sql(command, variables)

    def get_dialogue_statuses(self) -> List[Dict]:  # pragma: nocover
        """Read the statuses of all the dialog we are having."""
        data = self.execute_single_sql(
            "SELECT * FROM dialogue_statuses ORDER BY epoch DESC LIMIT 100"
        )
        results = []
        for datum in data:
            result = {}
            result["dialog_id"] = datum[0]
            result["epoch"] = datum[1]
            result["other_agent_key"] = datum[2]
            result["received_msg"] = datum[3]
            result["sent_msg"] = datum[4]
            results.append(result)

        return results

    def calc_uncleared_fet(self) -> int:  # pragma: nocover
        """Calc our uncleared fet."""
        cleared_fet_result = self.execute_single_sql(
            "SELECT amount FROM fet_table WHERE id=0"
        )
        if len(cleared_fet_result) != 0:
            uncleared_fet_result = self.execute_single_sql(
                "SELECT SUM(amount) FROM transaction_history WHERE status = 'in_progress'"
            )
            if len(uncleared_fet_result) == 0 or uncleared_fet_result[0][0] is None:
                return cleared_fet_result[0][0]
            return cleared_fet_result[0][0] + uncleared_fet_result[0][0]
        return -99

    def add_friendly_name(
        self, oef_key: str, friendly_name: str, is_self: bool = False
    ) -> None:  # pragma: nocover
        """Record the friendly name of one the agents we are dealing with (including ourselves)."""
        t = int(time.time())
        command = "INSERT OR REPLACE INTO name_lookup2(oef_key, friendly_name, epoch, is_self) VALUES(?, ?, ?, ?)"
        variables = (str(oef_key), str(friendly_name), t, 1 if is_self else 0)
        self.execute_single_sql(command, variables)

    def add_in_progress_transaction(
        self, tx: str, oef_key_payer: str, oef_key_payee: str, amount: int
    ) -> None:  # pragma: nocover
        """Record that a transaction in underway."""
        t = int(time.time())
        command = "INSERT OR REPLACE INTO transaction_history(tx, epoch, oef_key_payer, oef_key_payee, amount, status) VALUES(?, ?, ?, ?, ?, 'in_progress')"
        variables = (str(tx), t, str(oef_key_payer), str(oef_key_payee), amount)
        self.execute_single_sql(command, variables)

    def get_in_progress_transactions(self) -> List[Dict]:  # pragma: nocover
        """Read all in-progress transactions."""
        return self.get_transactions_with_status("in_progress")

    def get_complete_transactions(self) -> List[Dict]:  # pragma: nocover
        """Read all complete transactions."""
        return self.get_transactions_with_status("complete")

    def get_transactions_with_status(
        self, status: str
    ) -> List[Dict]:  # pragma: nocover
        """Read all transactions with a given status."""
        command = (
            "SELECT * from transaction_history WHERE status = ? ORDER BY epoch DESC"
        )
        variables = (str(status),)
        data = self.execute_single_sql(command, variables)
        results = []
        for datum in data:
            result = {}
            result["tx_hash"] = datum[0]
            result["epoch"] = datum[1]
            result["oef_key_payer"] = datum[2]
            result["oef_key_payee"] = datum[3]
            result["amount"] = datum[4]
            result["status"] = datum[5]
            results.append(result)

        return results

    def get_n_transactions(self, count: int) -> List[Dict]:  # pragma: nocover
        """Get the most resent N transactions."""
        command = "SELECT * from transaction_history ORDER BY epoch DESC LIMIT ?"
        variables = (count,)
        data = self.execute_single_sql(command, variables)
        results = []
        for datum in data:
            result = {}
            result["tx_hash"] = datum[0]
            result["epoch"] = datum[1]
            result["oef_key_payer"] = datum[2]
            result["oef_key_payee"] = datum[3]
            result["amount"] = datum[4]
            result["status"] = datum[5]
            results.append(result)

        return results

    def set_transaction_complete(self, tx: str) -> None:  # pragma: nocover
        """Set a specific transaction as complete."""
        command = "UPDATE transaction_history SET status ='complete' WHERE tx = ?"
        variables = (str(tx),)
        self.execute_single_sql(command, variables)

    def lookup_friendly_name(self, oef_key: str) -> Optional[str]:  # pragma: nocover
        """Look up friendly name given the OEF key."""
        command = "SELECT * FROM name_lookup2 WHERE oef_key = ? ORDER BY epoch DESC"
        variables = (str(oef_key),)
        results = self.execute_single_sql(command, variables)
        if len(results) == 0:
            return None
        return results[0][1]

    def lookup_self_names(
        self,
    ) -> Tuple[Optional[str], Optional[str]]:  # pragma: nocover
        """Return out own name and key."""
        results = self.execute_single_sql(
            "SELECT oef_key, friendly_name FROM name_lookup2 WHERE is_self = 1 ORDER BY epoch DESC"
        )
        if len(results) == 0:
            return None, None
        return results[0][0], results[0][1]

    def add_entry_no_save(
        self,
        raw_path: str,
        processed_path: str,
        total_count: int,
        moving_count: int,
        free_spaces: int,
        lat: float,
        lon: float,
    ) -> None:  # pragma: nocover
        """Add an entry into the detection database but do not save anything to disk."""
        # need to extract the time!
        t = self.extract_time_from_raw_path(raw_path)
        command = "INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        variables = (
            t,
            raw_path,
            processed_path,
            total_count,
            moving_count,
            free_spaces,
            lat,
            lon,
        )
        self.execute_single_sql(command, variables)

    def add_entry(
        self,
        raw_image: str,
        processed_image: str,
        total_count: int,
        moving_count: int,
        free_spaces: int,
        lat: float,
        lon: float,
    ) -> None:  # pragma: nocover
        """Add an entry into the detection database and record images to disk."""
        t = int(time.time())
        raw_path = self.generate_raw_image_path(t)
        processed_path = self.generate_processed_path(t)

        skimage.io.imsave(raw_path, raw_image)
        skimage.io.imsave(processed_path, processed_image)
        command = "INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        variables = (
            t,
            raw_path,
            processed_path,
            total_count,
            moving_count,
            free_spaces,
            lat,
            lon,
        )
        self.execute_single_sql(command, variables)

    def execute_single_sql(
        self,
        command: str,
        variables: Tuple[Union[str, int, float], ...] = (),
        print_exceptions: bool = True,
    ) -> List:
        """Query the database - all the other functions use this under the hood."""
        conn = None
        ret = []
        try:
            conn = sqlite3.connect(self.database_path, timeout=300)  # 5 mins
            c = conn.cursor()
            c.execute(command, variables)
            ret = c.fetchall()
            conn.commit()
        except Exception as e:  # pragma: nocover # pylint: disable=broad-except
            if print_exceptions:
                self.logger.warning("Exception in database: {}".format(e))
        finally:
            if conn is not None:
                conn.close()

        return ret

    def get_latest_detection_data(self, max_num_rows: int) -> List[Dict]:
        """Return the most recent detection data."""
        command = """SELECT * FROM images ORDER BY epoch DESC LIMIT ?"""
        variables = (max_num_rows,)
        results = self.execute_single_sql(command, variables)

        if results is None:
            return None
        ret_data = []
        for r in results:
            this_data = {}
            this_data["epoch"] = r[0]
            this_data["raw_image_path"] = r[1]
            this_data["processed_image_path"] = r[2]
            this_data["total_count"] = r[3]
            this_data["moving_count"] = r[4]
            this_data["free_spaces"] = r[5]
            this_data["lat"] = r[6]
            this_data["lon"] = r[7]
            ret_data.append(this_data)

        return ret_data

    def prune_image_table(self, max_entries: int) -> None:  # pragma: nocover
        """Remove image data if table longer than max_entries."""
        self.prune_table("images", max_entries)

    def prune_transaction_table(self, max_entries: int) -> None:  # pragma: nocover
        """Remove transaction data if table longer than max_entries."""
        self.prune_table("transaction_history", max_entries)

    def prune_table(self, table_name: str, max_entries: int) -> None:  # pragma: nocover
        """Remove any data if table longer than max_entries."""
        command = "SELECT epoch FROM ? ORDER BY epoch DESC LIMIT 1 OFFSET ?"
        variables = (
            table_name,
            max_entries - 1,
        )
        results = self.execute_single_sql(command=command, variables=variables)

        if len(results) != 0:
            last_epoch = results[0][0]
            command = """DELETE FROM ? WHERE epoch<?"""
            variables = (
                table_name,
                last_epoch,
            )
            self.execute_single_sql(command, variables)

    def ensure_dirs_exist(self) -> None:
        """Test if we have our temp directories, and if we don't create them."""
        if not os.path.isdir(self.temp_dir):
            os.mkdir(self.temp_dir)
        if not os.path.isdir(self.raw_image_dir):
            os.mkdir(self.raw_image_dir)
        if not os.path.isdir(self.processed_image_dir):
            os.mkdir(self.processed_image_dir)

    def generate_raw_image_path(self, t: int) -> str:  # pragma: nocover
        """Return path where we store raw images."""
        return (
            self.raw_image_dir
            + "{0:012d}".format(t)
            + "_raw_image"
            + self.image_file_ext
        )

    def generate_processed_path(self, t: int) -> str:  # pragma: nocover
        """Return path where we store processed images."""
        return (
            self.processed_image_dir
            + "{0:012d}".format(t)
            + "_processed_image"
            + self.image_file_ext
        )

    def generate_processed_from_raw_path(self, raw_name: str) -> str:  # pragma: nocover
        """Given the raw path, return the processes path."""
        return raw_name.replace("_raw_image.", "_processed_image.").replace(
            self.raw_image_dir, self.processed_image_dir
        )

    def extract_time_from_raw_path(self, raw_name: str) -> int:  # pragma: nocover
        """Given the raw path name, return the time the detection happened."""
        start_index = len(self.raw_image_dir)
        extracted_num = raw_name[start_index : start_index + self.num_digits_time]
        return int(extracted_num)
