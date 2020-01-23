import sqlite3
import datetime
from typing import Dict, Union
import logging
import os.path

logger = logging.getLogger(__name__)
my_path = os.path.dirname(__file__)
DB_SOURCE = os.path.join(my_path, "thermo_data.db")

con = sqlite3.connect(DB_SOURCE)
cur = con.cursor()

cur.close()
con.commit()
cur.close()
command = """CREATE TABLE IF NOT EXISTS data ( internal_temp REAL,
                                               idx TEXT)"""
con = sqlite3.connect(DB_SOURCE)
cur = con.cursor()
cur.execute(command)
cur.close()
con.commit()
if con is not None:
    logger.debug("Thermometer: I closed the db after checking if it is populated")
    con.close()

class TemperData():
    """Represents the Data from the database."""

    def add_data(self, temprature: float) -> None:
        """
        Add data to the database.

        :param temprature: the internal temprature
        :return: None
        """
        con = sqlite3.connect(DB_SOURCE)
        cur = con.cursor()
        cur.execute(""" INSERT INTO data ( internal_temp, idx) VALUES (?,?)""",(temprature, datetime.datetime.now().strftime("%s")),)
        logger.info("Theremometer: I added data in the db!")
        cur.close()
        con.commit()
        con.close()

    def get_data_for_specific_dates(self, start_date:str, end_date: str) -> Dict[str, int]:
        con = sqlite3.connect(DB_SOURCE)
        cur = con.cursor()
        start_dt = datetime.datetime.strptime(start_date,"%d/%m/%Y")
        start = start_dt.strftime("%s")
        end_dt = datetime.datetime.strptime(end_date,"%d/%m/%Y")
        end = end_dt.strftime("%s")
        cur.execute("SELECT * FROM data WHERE idx BETWEEN ? and ?", (str(start),str(end)))
        data = cast(Dict[str, int], cur.fetchaill())
        cur.close()
        con.commit()
        con.close()
        return data