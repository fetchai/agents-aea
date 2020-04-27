The AEA generic seller with ORM integration demonstrate how to interact with a database using python-sql objects.

* The provider of a service in the form of data retrieved from a database.
* The buyer of a service.

### Discussion

Object-relational-mapping is the idea of being able to write SQL queries, using the object-oriented paradigm of your preferred programming language.
The scope of the specific demo is to demonstrate how to create an easy configurable AEA that reads data from a database using ORMs. 
This demo will not use any smart contract, because these would be out of the scope of the tutorial.

- We assume, that you followed the guide for the <a href="/generic-skills/"> generic-skills. </a>
- We assume, that we have a database `genericdb.db` with table name `data`. This table contains the following columns `timestamp` and `thermometer`
- We assume, that we have a hardware thermometer sensor that adds the readings in the `genericdb` database

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file. 

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.
   
### Launch an OEF search and communication node

In a separate terminal, launch a local [OEF search and communication node](../oef-ledger).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo: Ledger payment

A demo to run a scenario with a true ledger transaction on Fetch.ai `testnet` network or Ethereum `ropsten` network. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

### Create the seller AEA (ledger version)

Create the AEA that will provide data.

``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/generic_seller:0.2.0
```

### Create the buyer client (ledger version)

In another terminal, create the AEA that will query the seller AEA.

``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/generic_buyer:0.2.0
```

Additionally, create the private key for the buyer AEA based on the network you want to transact.

To generate and add a key for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

To generate and add a key for Ethereum use:
``` bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `my_seller_aea/aea-config.yaml` and
`my_buyer_aea/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect

To connect to Fetchai:

``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

To connect to Ethereum:
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Update the seller and buyer AEA skill configs

In `my_seller_aea/vendor/fetchai/generic_seller/skill.yaml`, replace the `data_for_sale`, `search_schema`, and `search_data` with your data:
``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |
|  dialogues:                       |  dialogues:                      |
|    args: {}                       |    args: {}                      |
|    class_name: Dialogues          |    class_name: Dialogues         |
|  strategy:                        |  strategy:                       |
|    class_name: Strategy           |    class_name: Strategy          |
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
|dependencies:                      |dependencies:                     |
|  SQLAlchemy: {}                   |  SQLAlchemy: {}                  |    
|----------------------------------------------------------------------|
```
The `search_schema` and the `search_data` are used to register the service in the [OEF search node](../oef-ledger) and make your agent discoverable. The name of each attribute must be a key in the `search_data` dictionary.

In the generic buyer skill config (`my_buyer_aea/skills/generic_buyer/skill.yaml`) under strategy change the `currency_id`,`ledger_id`, and at the bottom of the file the `ledgers`.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |  
|  dialogues:                       |  dialogues:                      |
|    args: {}                       |    args: {}                      |
|    class_name: Dialogues          |    class_name: Dialogues         |
|  strategy:                        |  strategy:                       |
|    class_name: Strategy           |    class_name: Strategy          |
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
After changing the skill config files you should run the following command for both agents to install each dependency:
``` bash
aea install
```

### Modify the seller's strategy

Open the `strategy.py` with your IDE and modify the following.

Import the newly installed library to your strategy.
``` python
import sqlalchemy as db
```
Then modify your strategy's \_\_init__ function to match the following code:
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
        self._scheme = kwargs.pop("search_data")
        self._datamodel = kwargs.pop("search_schema")
        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)
        data_for_sale = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)

        super().__init__(**kwargs)

        self._oef_msg_id = 0
        self._db_engine = db.create_engine("sqlite:///genericdb.db")
        self._tbl = self.create_database_and_table()
        self.insert_data()

        # Read the data from the sensor if the bool is set to True.
        # Enables us to let the user implement his data collection logic without major changes.
        if self._has_data_source:
            self._data_for_sale = self.collect_from_data_source()
        else:
            self._data_for_sale = data_for_sale
``` 

At the end of the file modify the `collect_from_data_source` function : 
``` python
    def collect_from_data_source(self) -> Dict[str, Any]:
        """Implement the logic to collect data."""
        connection = self._db_engine.connect()
        query = db.select([self._tbl])
        result_proxy = connection.execute(query)
        data_points = result_proxy.fetchall()
        return {"data": json.dumps(list(map(tuple, data_points)))}
```
Also, create two new functions, one that will create a connection with the database, and another one will populate the database with some fake data:

``` python
    def create_database_and_table(self):
        """Creates a database and a table to store the data if not exists."""
        metadata = db.MetaData()

        tbl = db.Table(
            "data",
            metadata,
            db.Column("timestamp", db.Integer()),
            db.Column("temprature", db.String(255), nullable=False),
        )
        metadata.create_all(self._db_engine)
        return tbl

    def insert_data(self):
        """Insert data in the database."""
        connection = self._db_engine.connect()
        self.context.logger.info("Populating the database...")
        for _ in range(10):
            query = db.insert(self._tbl).values(  # nosec
                timestamp=time.time(), temprature=str(random.randrange(10, 25))
            )
            connection.execute(query)
```

### Fund the buyer AEA

To create some wealth for your buyer AEA based on the network you want to transact with:

On the Fetch.ai `testnet` network.
``` bash
aea generate-wealth fetchai
```

On the Ethereum `rospten` network.
``` bash
aea generate-wealth ethereum
```

## Run the AEAs

You can change the endpoint's address and port by modifying the connection's yaml file (my_seller_aea/connection/oef/connection.yaml)

Under config locate :

``` bash
addr: ${OEF_ADDR: 127.0.0.1}
```
 and replace it with your ip (The ip of the machine that runs the oef image.)

Run both AEAs from their respective terminals

``` bash 
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
aea run --connections fetchai/oef:0.2.0
```
You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

## Delete the AEAs
When you're done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the seller AEA to the buyer. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Buyer_AEA
        participant Seller_AEA
        participant Blockchain
    
        activate Buyer_AEA
        activate Search
        activate Seller_AEA
        activate Blockchain
        
        Seller_AEA->>Search: register_service
        Buyer_AEA->>Search: search
        Search-->>Buyer_AEA: list_of_agents
        Buyer_AEA->>Seller_AEA: call_for_proposal
        Seller_AEA->>Buyer_AEA: propose
        Buyer_AEA->>Seller_AEA: accept
        Seller_AEA->>Buyer_AEA: match_accept
        Buyer_AEA->>Blockchain: transfer_funds
        Buyer_AEA->>Seller_AEA: send_transaction_hash
        Seller_AEA->>Blockchain: check_transaction_status
        Seller_AEA->>Buyer_AEA: send_data
        
        deactivate Buyer_AEA
        deactivate Search
        deactivate Seller_AEA
        deactivate Blockchain
       
</div>


