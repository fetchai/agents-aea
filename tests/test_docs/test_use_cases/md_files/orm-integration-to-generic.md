``` bash 
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
``` 
``` bash 
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/generic_seller:0.1.0
``` 
``` bash 
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/generic_buyer:0.1.0
``` 
``` bash 
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
``` 
``` bash 
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
``` 
``` yaml 
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      total_price: 10              |      total_price: 10             |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      has_data_source: True        |      has_data_source: True       |
|      data_for_sale: {}            |      data_for_sale: {}           |
|      search_schema:               |      search_schema:              |
|        attribute_one:             |        attribute_one:            |
|          name: country            |          name: country           |
|          type: str                |          type: str               |
|          is_required: True        |          is_required: True       |
|        attribute_two:             |        attribute_two:            |
|          name: city               |          name: city              |
|          type: str                |          type: str               |
|          is_required: True        |          is_required: True       |
|      search_data:                 |      search_data:                |
|        country: UK                |        country: UK               |
|        city: Cambridge            |        city: Cambridge           |
|dependencies                       |dependencies:                     |
|  SQLAlchemy: {}                   |  SQLAlchemy: {}                  |    
|----------------------------------------------------------------------| 
``` 
``` yaml 
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      max_price: 40                |      max_price: 40               |
|      max_buyer_tx_fee: 100        |      max_buyer_tx_fee: 200000    |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      search_query:                |      search_query:               |
|        search_term: country       |        search_term: country      |
|        search_value: UK           |        search_value: UK          |
|        constraint_type: '=='      |        constraint_type: '=='     |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
``` 
``` bash 
aea install
``` 
``` bash 
aea generate-wealth fetchai
``` 
``` bash 
aea generate-wealth ethereum
``` 
``` bash 
addr: ${OEF_ADDR: 127.0.0.1}
``` 
``` bash 
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
``` 
``` bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
``` 
``` yaml 
ledger_apis:
  fetchai:
    network: testnet
``` 
``` yaml 
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
``` 
``` python 
import sqlalchemy as db
``` 
``` python 
  def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._seller_tx_fee = kwargs.pop("seller_tx_fee", DEFAULT_SELLER_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self._total_price = kwargs.pop("total_price", DEFAULT_TOTAL_PRICE)
        self._has_data_source = kwargs.pop("has_data_source", DEFAULT_HAS_DATA_SOURCE)

        self._db_engine = db.create_engine('sqlite:///genericdb.db')
        self._tbl = self.create_database_and_table()
        self.insert_data()

        # Read the data from the sensor if the bool is set to True.
        # Enables us to let the user implement his data collection logic without major changes.
        if self._has_data_source:
            self._data_for_sale = self.collect_from_data_source()
        else:
            self._data_for_sale = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)

        super().__init__(**kwargs)
        self._oef_msg_id = 0

        self._scheme = kwargs.pop("search_data")
        self._datamodel = kwargs.pop("search_schema")
``` 
``` python 
    def collect_from_data_source(self) -> Dict[str, Any]:
        connection = self._db_engine.connect()
        query = db.select([self._tbl])
        result_proxy = connection.execute(query)
        return {"data": result_proxy.fetchall()}
``` 
``` python 
    def create_database_and_table(self):
        """Creates a database and a table to store the data if not exists."""
        metadata = db.MetaData()

        tbl = db.Table('data', metadata,
                       db.Column('timestamp', db.Integer()),
                       db.Column('temprature', db.String(255), nullable=False),
              )
        metadata.create_all(self._db_engine)
        return tbl

    def insert_data(self):
        """Insert data in the database."""
        connection = self._db_engine.connect()
        logger.info("Populating the database....")
        for counter in range(10):
            query = db.insert(self._tbl).values(timestamp=time.time(), temprature=str(random.randrange(10, 25)))
            connection.execute(query)
``` 
