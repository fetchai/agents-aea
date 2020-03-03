The AEA car-park skills demonstrate an interaction between two AEAs.

* The carpark_detection AEA provides information on the number of car parking spaces available in a given vicinity.
* The carpark_client AEA is interested in purchasing information on available car parking spaces in the same vicinity.

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

##Discussion
The full Fetch.ai car park AEA demo is documented in its own repo [here](https://github.com/fetchai/carpark_agent).
This demo allows you to test the AEA functionality of the car park AEA demo without the detection logic.

It demonstrates how the AEAs trade car park information.


### Launch the OEF

In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following.

## Demo instructions: Ledger payment

### Create car detector AEA

First, create the car detector AEA:
``` bash
aea create car_detector
cd car_detector
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/carpark_detection:0.1.0
aea install
```

Alternatively to the previous two steps, simply run:
``` bash
aea fetch fetchai/car_detector:0.1.0
cd car_detector
aea install
```

### Create car data buyer AEA

Then, create the car data client AEA:
``` bash
aea create car_data_buyer
cd car_data_buyer
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/carpark_client:0.1.0
aea install
```

Alternatively to the previous two steps, simply run:
``` bash
aea fetch fetchai/car_data_buyer:0.1.0
cd car_data_buyer
aea install
```

Additionally, create the private key for the car data buyer AEA based on the network you want to transact.

To generate and add a private-public key pair for Fetch.ai use:
```bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

To generate and add a private-public key pair for Ethereum use:
```bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `car_detector/aea-config.yaml` and
`car_data_buyer/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect.

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

### Generate wealth for the car data buyer AEA

Create some wealth for your car data buyer based on the network you want to transact with: 

On the Fetch.ai `testnet` network.
``` bash
aea generate-wealth fetchai
```

On the Ethereum `ropsten` . (It takes a while).
``` bash
aea generate-wealth ethereum
```

### Update the skill configs

In the carpark detection skill config (`car_detector/vendor/fetchai/skills/carpark_detection/skill.yaml`) under strategy, amend the `currency_id`, `ledger_id`, and `db_is_rel_to_cwd` as follows.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      data_price_fet: 2000         |      data_price_fet: 2000        |
|      db_is_rel_to_cwd: False      |      db_is_rel_to_cwd: False     |
|      db_rel_dir: ../temp_files    |      db_rel_dir: ../temp_files   |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|----------------------------------------------------------------------| 
```

An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.carpark_detection.models.strategy.args.db_is_rel_to_cwd False --type bool
```

In the carpark data buyer skill config (`car_data_buyer/vendor/fetchai/skills/carpark_client/skill.yaml`) under strategy change the `currency_id` and `ledger_id`.

``` yaml
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|models:                            |models:                           |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      country: UK                  |      country: UK                 |
|      search_interval: 120         |      search_interval: 120        |
|      no_find_search_interval: 5   |      no_find_search_interval: 5  |
|      max_price: 40000             |      max_price: 40000            |
|      max_detection_age: 36000000  |      max_detection_age: 36000000 |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      max_buyer_tx_fee: 6000       |      max_buyer_tx_fee: 6000      |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

Another way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.max_buyer_tx_fee 6000 --type int
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.carpark_client.models.strategy.args.ledger_id ethereum
```

### Run both AEAs

Finally, run both AEAs from their respective directories:
``` bash
aea run --connections fetchai/oef:0.1.0
```

You can see that the AEAs find each other, negotiate and eventually trade.

### Cleaning up

When you're finished, delete your AEAs:
``` bash
cd ..
aea delete car_detector
aea delete car_data_buyer
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the car park AEA to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Car_Data_Buyer_AEA
        participant Car_Park_AEA
        participant Blockchain
    
        activate Car_Data_Buyer_AEA
        activate Search
        activate Car_Park_AEA
        activate Blockchain
        
        Car_Park_AEA->>Search: register_service
        Car_Data_Buyer_AEA->>Search: search
        Search-->>Car_Data_Buyer_AEA: list_of_agents
        Car_Data_Buyer_AEA->>Car_Park_AEA: call_for_proposal
        Car_Park_AEA->>Car_Data_Buyer_AEA: propose
        Car_Data_Buyer_AEA->>Car_Park_AEA: accept
        Car_Park_AEA->>Car_Data_Buyer_AEA: match_accept
        Car_Data_Buyer_AEA->>Blockchain: transfer_funds
        Car_Data_Buyer_AEA->>Car_Park_AEA: send_transaction_hash
        Car_Park_AEA->>Blockchain: check_transaction_status
        Car_Park_AEA->>Car_Data_Buyer_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Car_Park_AEA
        deactivate Blockchain
</div>

<br />



