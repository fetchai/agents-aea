The AEA framework uses models that enable us to create custom behaviour for each agent. Moreover, the framework enables us to use third-party libraries 
hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file.

## How to connect a database

### Option 1

Create a new model that will handle the database communication. It will be responsible for inserting or retrieving data from the database. Through the context
of the agent, we can get these data from the skills of the AEA. 

For example:

```python
import datetime
import os.path
import sqlite3
from typing import Dict, cast

my_path = os.path.dirname(__file__)

DB_SOURCE = os.path.join(my_path, "dummy_weather_station_data.db")


class DBCommunication:
    """A class to communicate with a database."""

    def __init__(self):
        """
        Initialize the database communication.

        :param source: the source
        """
        self.source = DB_SOURCE

    def db_connection(self) -> sqlite3.Connection:
        """
        Get db connection.

        :return: the db connection
        """
        con = sqlite3.connect(self.source)
        return con

    def get_data_for_specific_dates(
        self, start_date: str, end_date: str
    ) -> Dict[str, int]:
        """
        Get data for specific dates.

        :param start_date: the start date
        :param end_date: the end date
        :return: the data
        """
        con = self.db_connection()
        cur = con.cursor()
        start_dt = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        start = start_dt.strftime("%s")
        end_dt = datetime.datetime.strptime(end_date, "%d/%m/%Y")
        end = end_dt.strftime("%s")
        cur.execute(
            "SELECT * FROM data WHERE idx BETWEEN ? AND ?", (str(start), str(end))
        )
        data = cast(Dict[str, int], cur.fetchall())
        cur.close()
        con.close()
        return data
```

The above script creates a database communication class that then we instantiate inside the strategy model of the weather_station package and we fetch data before
we generate the proposal for the client.

### Option 2

The other option is to use ORM (Object-relational-mapping). Object-relational-mapping is the idea of being able to write SQL queries, using the object-oriented paradigm of your preferred programming language.

To use this, you will have to list the ORM package in the dependencies of your skill and then run the `aea install` command before the `aea run`

Lastly, you have to implement the logic inside a class that inherits from the Model abstract class. For a detailed example of how to use ORM follow the 
<a href='/orm-integration-to-generic/'>ORM use case</a>



