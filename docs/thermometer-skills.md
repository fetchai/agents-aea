The AEA thermometer skills demonstrate an interaction between two AEAs.

* The provider of thermometer data (the thermometer).
* The buyer of thermometer data (the thermometer_client).

### Discussion

The scope of the specific demo is to demonstrate how to create a very simple AEA with the usage of the AEA framework, a Raspberry Pi, and a thermometer sensor. The thermometer AEA
will read data from the sensor each time a client requests and will deliver to the client upon payment. To keep the demo simple we avoided the usage of a database since this would increase the complexity. As a result, the AEA can provide only one reading from the sensor.
This demo does not utilise a smart contract. As a result, we interact with a ledger only to complete a transaction.

Since the AEA framework enables us to use third-party libraries hosted on PyPI we can directly reference the external dependencies.
The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file. 
The AEA must run inside a Raspberry Pi or any other Linux system, and the sensor must be connected to the USB port.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions: Ledger payment

A demo to run the thermometer scenario with a true ledger transaction on Fetch.ai `testnet` or Ethereum `ropsten` network. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

### Create the thermometer AEA

Create the AEA that will provide thermometer measurements.

``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer:0.1.0
aea install
```

### Create the thermometer client

In another terminal, create the AEA that will query the thermometer AEA.

``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer_client:0.1.0
aea install
```

Additionally, create the private key for the weather_client AEA based on the network you want to transact.

To generate and add a key for Fetch.ai use:
```bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

To generate and add a key for Ethereum use:
```bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `my_thermometer_aea/aea-config.yaml` and
`my_thermometer_client/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect.

To connect to Fetchai:
``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

To connect to Ethereum:
```yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Fund the thermometer client AEA

Create some wealth for your weather client based on the network you want to transact with: 

On the Fetch.ai `testnet` network.
``` bash
aea generate-wealth fetchai
```

On the Ethereum `ropsten` . (It takes a while).
``` bash
aea generate-wealth ethereum
```

### Update the skill configs

In the thermometer skill config (`my_thermometer_aea/vendor/fetchai/skills/thermometer/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      price_per_row: 1             |      price_per_row: 1            |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      has_sensor: True             |      has_sensor: True            |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|----------------------------------------------------------------------| 
```

An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer.models.strategy.args.ledger_id ethereum
```

In the thermometer client skill config (`my_thermometer_client/vendor/fetchai/skills/thermometer_client/skill.yaml`) under strategy change the `currency_id` and `ledger_id`.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      max_price: 4                 |      max_price: 40               |
|      max_buyer_tx_fee: 1          |      max_buyer_tx_fee: 200000    |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.max_buyer_tx_fee 10000 --type int
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer_client.models.strategy.args.ledger_id ethereum
```

## Run the AEAs

#### Important: Your thermometer AEA must run on your Raspberry Pi and the sensor must be connected to the usb.

You can change the end point's address and port by modifying the connection's yaml file (my_thermometer_aea/connection/oef/connection.yaml)

Under config locate :

``` yaml
addr: ${OEF_ADDR: 127.0.0.1}
```
 and replace it with your ip (The ip of the machine that runs the oef image.)

Run both AEAs from their respective terminals

```bash 
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
```
You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

## Delete the AEAs
When you're done, go up a level and delete the AEAs.
```bash 
cd ..
aea delete my_thermometer_aea
aea delete my_thermometer_client
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the thermometer AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Thermometer_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Thermometer_AEA
        activate Blockchain
        
        Thermometer_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Thermometer_AEA: call_for_proposal
        Thermometer_AEA->>Client_AEA: propose
        Client_AEA->>Thermometer_AEA: accept
        Thermometer_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Thermometer_AEA: send_transaction_hash
        Thermometer_AEA->>Blockchain: check_transaction_status
        Thermometer_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Thermometer_AEA
        deactivate Blockchain
       
</div>
