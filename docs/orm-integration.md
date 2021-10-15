This guide demonstrates how to configure an AEA to interact with a database using `python-sql` objects.

## Discussion

Object-relational-mapping (ORM) is the idea of being able to write SQL queries, using the object-oriented paradigm of your preferred programming language. The scope of this guide is to demonstrate how you can create an easily configurable AEA that reads data from a database using ORMs.

- We assume, that you followed the guide for the <a href="../thermometer-skills/"> thermometer-skills. </a>
- We assume, that we have a database `genericdb.db` with table name `data`. This table contains the following columns `timestamp` and `thermometer`.
- We assume, that we have a hardware thermometer sensor that adds the readings in the `genericdb` database (although you can follow the guide without having access to a sensor).

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies. The `aea install` command will install each dependency that the specific AEA needs and which is listed in the skill's YAML file. 

## Communication

This diagram shows the communication between the various entities in the case where the thermometer data is successfully sold by the seller AEA to the buyer. 

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

This demo involves a true ledger transaction on Fetch.ai's `testnet` network or Ethereum's `ropsten`. This demo assumes the buyer trusts the seller AEA to send the data upon successful payment.

### Create the seller AEA

First, fetch the seller AEA which provides thermometer data:
``` bash
aea fetch fetchai/thermometer_aea:0.29.0 --alias my_thermometer_aea
cd my_thermometer_aea
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the seller from scratch:
``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/thermometer:0.26.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```

</p>
</details>


### Create the buyer client

In another terminal, fetch the buyer AEA:
``` bash
aea fetch fetchai/thermometer_client:0.30.0 --alias my_thermometer_client
cd my_thermometer_client
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create the car data client from scratch:
``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/thermometer_client:0.25.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```

</p>
</details>


### Add keys for the seller AEA

First, create the private key for the seller AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai `StargateWorld` use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Next, create a private key used to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```

### Add keys and generate wealth for the buyer AEA

The buyer needs to have some wealth to purchase the thermometer data.

First, create the private key for the buyer AEA based on the network you want to transact. To generate and add a private-public key pair for Fetch.ai use:
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```

Then, create some wealth for the buyer based on the network you want to transact with. On the Fetch.ai `StargateWorld` network:
``` bash
aea generate-wealth fetchai
```

Next, create a private key used to secure the AEA's communications:
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the key for use by the connections that request that:
``` bash
aea issue-certificates
```


### Update the seller and buyer AEA skill configurations

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
        latitude: 51.5194
        longitude: 0.127
      service_data:
        key: seller_service
        value: thermometer_data
      service_id: thermometer_data
      unit_price: 10
    class_name: Strategy
dependencies:
  SQLAlchemy: {}
```
The `service_data` is used to register the service in the <a href="../simple-oef">SOEF search node</a> and make your agent discoverable.

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
        latitude: 51.5194
        longitude: 0.127
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

After changing the skill configuration files you should run the following command for both agents to install each dependency:
``` bash
aea install
```

### Modify the seller's strategy

Before being able to modify a package we need to eject it from vendor:

``` bash
aea eject skill fetchai/thermometer:0.26.0
```

This will move the package to your `skills` directory and reset the version to `0.1.0` and the author to your author handle.

Open `strategy.py` (in `my_thermometer_aea/skills/thermometer/strategy.py`) and make the following modifications:

Import the newly installed `sqlalchemy` library in your strategy.
``` python
import sqlalchemy as db
```
Then modify your strategy's `__init__` function to match the following code:
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

At the end of the file modify the `collect_from_data_source` function: 
``` python
    def collect_from_data_source(self) -> Dict[str, str]:
        """Implement the logic to collect data."""
        connection = self._db_engine.connect()
        query = db.select([self._tbl])
        result_proxy = connection.execute(query)
        data_points = result_proxy.fetchall()
        return {"data": json.dumps(list(map(tuple, data_points)))}
```
Also, create two new functions, one that creates a connection with the database, and another that populates the database with some fake data. This is needed in the case you do not have access to an actual thermometer sensor that inserts data in the database.

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

First, run the thermometer (seller) AEA:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of this address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.)
This is the entry peer address for the local <a href="../acn">agent communication network</a> created by the thermometer AEA.

Then, configure the thermometer client (buyer) to connect to this same local ACN by running the following command in the buyer terminal, replacing `SOME_ADDRESS` with the value you noted above:
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```

Then run the thermometer client AEA:
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the configured testnet.

## Delete the AEAs

When you're done, stop the agents (`CTRL+C`), go up a level and delete the AEAs.
``` bash 
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```