This guide demonstrates how to configure an AEA to interact with a database using python-sql objects.

## Discussion

Object-relational-mapping is the idea of being able to write SQL queries, using the object-oriented paradigm of your preferred programming language. The scope of the specific demo is to demonstrate how to create an easy configurable AEA that reads data from a database using ORMs.

- We assume, that you followed the guide for the <a href="../thermometer-skills/"> thermometer-skills. </a>
- We assume, that we have a database `genericdb.db` with table name `data`. This table contains the following columns `timestamp` and `thermometer`
- We assume, that we have a hardware thermometer sensor that adds the readings in the `genericdb` database (although you can follow the guide without having access to a sensor).

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies. The `aea install` command will install each dependency that the specific AEA needs and which is listed in the skill's YAML file. 

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

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo instructions

A demo to run a scenario with a true ledger transaction on Fetch.ai `testnet` network or Ethereum `ropsten` network. This demo assumes the buyer trusts the seller AEA to send the data upon successful payment.

### Create the seller AEA

First, fetch the seller AEA, which will provide data:
``` bash
aea fetch fetchai/thermometer_aea:0.9.0 --alias my_thermometer_aea
cd my_thermometer_aea
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the seller from scratch:
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/p2p_libp2p:0.8.0
aea add connection fetchai/soef:0.7.0
aea add connection fetchai/ledger:0.4.0
aea add skill fetchai/thermometer:0.10.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
```

In `my_thermometer_aea/aea-config.yaml` add 
``` yaml
default_routing:
  fetchai/ledger_api:0.3.0: fetchai/ledger:0.4.0
  fetchai/oef_search:0.5.0: fetchai/soef:0.7.0
```

</p>
</details>


### Create the buyer client

In another terminal, fetch the AEA that will query the seller AEA.
``` bash
aea fetch fetchai/thermometer_client:0.9.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the car data client from scratch:
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/p2p_libp2p:0.8.0
aea add connection fetchai/soef:0.7.0
aea add connection fetchai/ledger:0.4.0
aea add skill fetchai/thermometer_client:0.9.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.8.0
```

In `my_buyer_aea/aea-config.yaml` add 
``` yaml
default_routing:
  fetchai/ledger_api:0.3.0: fetchai/ledger:0.4.0
  fetchai/oef_search:0.5.0: fetchai/soef:0.7.0
```

</p>
</details>


### Add keys for the thermometer AEA

First, create the private key for the thermometer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `AgentLand` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

### Add keys and generate wealth for the thermometer client AEA

The thermometer client needs to have some wealth to purchase the thermometer information.

First, create the private key for the thermometer client AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
aea add-key fetchai fetchai_private_key.txt --connection
```

Then, create some wealth for your thermometer client based on the network you want to transact with. On the Fetch.ai `testnet` network:
``` bash
aea generate-key fetchai
```


### Update the seller and buyer AEA skill configs

In `my_thermometer_aea/vendor/fetchai/skills/thermometer/skill.yaml`, replace the `data_for_sale` with your data:
``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      data_for_sale:
        temperature: 26
      has_data_source: false
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 0.127
        longitude: 51.5194
      service_data:
        key: seller_service
        value: thermometer_data
      service_id: thermometer_data
      unit_price: 10
    class_name: Strategy
dependencies:
  SQLAlchemy: {}
```
The `data_model` and the `service_data` are used to register the service in the <a href="../simple-oef">SOEF search node</a> and make your agent discoverable. The name of each attribute must be a key in the `service_data` dictionary.

In `my_thermometer_client/vendor/fetchai/skills/thermometer_client/skill.yaml`) ensure you have matching data.

``` yaml
models:
  ...
  strategy:
    args:
      currency_id: FET
      is_ledger_tx: true
      ledger_id: fetchai
      location:
        latitude: 0.127
        longitude: 51.5194
      max_negotiations: 1
      max_tx_fee: 1
      max_unit_price: 20
      search_query:
        constraint_type: ==
        search_key: seller_service
        search_value: thermometer_data
      search_radius: 5.0
      service_id: thermometer_data
    class_name: Strategy
```

After changing the skill config files you should run the following command for both agents to install each dependency:
``` bash
aea install
```

### Modify the seller's strategy

Before being able to modify a package we need to eject it from vendor:

``` bash
aea eject skill fetchai/thermometer:0.10.0
```

This will move the package to your `skills` directory and reset the version to `0.1.0` and the author to your author handle.

Open the `strategy.py` (in `my_thermometer_aea/skills/thermometer/strategy.py`) with your IDE and modify the following.

Import the newly installed library to your strategy.
``` python
import sqlalchemy as db
```
Then modify your strategy's \_\_init__ function to match the following code:
``` python
class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._db_engine = db.create_engine("sqlite:///genericdb.db")
        self._tbl = self.create_database_and_table()
        self.insert_data()
        super().__init__(**kwargs)
``` 

At the end of the file modify the `collect_from_data_source` function : 
``` python
    def collect_from_data_source(self) -> Dict[str, str]:
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
        for _ in range(10):
            query = db.insert(self._tbl).values(  # nosec
                timestamp=time.time(), temprature=str(random.randrange(10, 25))
            )
            connection.execute(query)
```

After modifying the skill we need to fingerprint it:

``` bash
aea fingerprint skill {YOUR_AUTHOR_HANDLE}/thermometer:0.1.0
```

### Run both AEAs

Run both AEAs from their respective terminals.

First, run the thermometer AEA:

``` bash
aea run
```

Once you see a message of the form `My libp2p addresses: ['SOME_ADDRESS']` take note of the address.

Then, update the configuration of the thermometer client AEA's p2p connection (in `vendor/fetchai/connections/p2p_libp2p/connection.yaml`) replace the following:

``` yaml
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```

where `SOME_ADDRESS` is replaced accordingly.

Then run the thermometer client AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the configured testnet.

## Delete the AEAs

When you're done, go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```
