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

"""This package contains the Database Communication for the weather agent."""

import psycopg2
import datetime


class Db_communication():
    """Contains the functionality for communicating with the db."""

    def __init__(self, source):
        """Initialize the variables for the db."""
        self.source = source

    def db_connection(self):
        """Connect to the database."""
        con = None
        print(self.source)
        if self.source == "fake":
            con = psycopg2.connect('dbname =  weather_fake')
        else:
            con = psycopg2.connect('dbname =  weather')

        con.autocommit = True
        return con

    def specific_dates(self, start, end):
        """Search the db for the specific dates."""
        con = self.db_connection()
        cur = con.cursor()
        print(start)
        print(end)
        if type(start) is str:
            start = datetime.datetime.strptime(start, '%d/%m/%Y')
            start = start.strftime('%s')
        if type(end) is str:
            end = datetime.datetime.strptime(end, '%d/%m/%Y')
            end = end.strftime('%s')
        command = "SELECT * FROM data WHERE idx BETWEEN %s::Text AND %s::Text"
        cur.execute(command, (float(start), float(end),))
        data = cur.fetchall()

        cur.close()
        con.close()
        return data
