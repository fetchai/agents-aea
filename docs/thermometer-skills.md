The AEA thermometer skills demonstrate an interaction between two AEAs.

* The provider of thermometer data (the thermometer).
* The buyer of thermometer data (the thermometer client).

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

##Discussion

The scope of the specific demo is to demonstrate how to create a very simple AEA with the usage of the AEA framework, a Raspberry Pi, and a thermometer sensor. The thermometer AEA
will read data from the sensor each time a client requests and will deliver to the client upon payment. To keep the demo simple we avoided the usage of a database since this would increase the complexity. As a result, the AEA can provide only one reading from the sensor.
Another step that we avoided is the usage of a smart contract that could store the readings from the sensor. As a result, we interact with a ledger only to complete a transaction.

Since the AEA framework enables us to use third-party libraries we don't have to do something to be able to read from the sensor. The `aea install` command will install each dependency that the specific AEA needs and is listed in the skill's YAML file. 
Though the AEA must run inside a Raspberry Pi or any other Linux system, and the sensor must be connected to the USB port.

### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo 1: Fetch.ai ledger payment

A demo to run the thermometer scenario with a true ledger transaction on Fetch.ai `testnet`. This demo assumes the thermometer
client trusts the thermometer AEA to send the data upon successful payment.

### Create the thermometer AEA (ledger version)

Create the AEA that will provide thermometer measurements.

``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer:0.1.0
aea install
```

### Create the thermometer client (ledger version)

In another terminal, create the AEA that will query the thermometer AEA.

``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer_client:0.1.0
aea install
```

Additionally, create the private key for the thermometer client AEA.
```bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

### Update the AEA configs

Both in `my_thermometer_aea/aea-config.yaml` and
`my_thermometer_client/aea-config.yaml`, replace `ledger_apis: {}` with the following.

``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

### Fund the thermometer client AEA

Create some wealth for your thermometer client on the Fetch.ai `testnet`. (It takes a while).
``` bash
aea generate-wealth fetchai
```

### Update the skill configs

Tell the thermometer client skill of the thermometer client AEA that we want to settle the transaction on the ledger:
``` bash
aea config set vendor.fetchai.skills.thermometer_client.shared_classes.strategy.args.is_ledger_tx True --type bool
```

Similarly, for the thermometer skill of the thermometer AEA:
``` bash
aea config set vendor.fetchai.skills.thermometer.shared_classes.strategy.args.is_ledger_tx True --type bool
```

## Run the AEAs

#### Important: Your thermometer AEA must run on your Raspberry Pi and the sensor must be connected to the usb.

You can change the end point's address and port by modifying the connection's yaml file (my_thermometer_aea/connection/oef/connection.yaml)

Under config locate :

```bash
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
## Demo instructions 2: Ethereum ledger payment

A demo to run the same scenario but with a true ledger transaction on the Ethereum Ropsten `testnet`. 
This demo assumes the thermometer client trusts the thermometer AEA to send the data upon successful payment.

### Create the thermometer AEA (ledger version)

Create the AEA that will provide thermometer measurements.

``` bash
aea create my_thermometer_aea
cd my_thermometer_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer:0.1.0
aea install
```

### Create the thermometer client (ledger version)

In another terminal, create the AEA that will query the thermometer AEA.

``` bash
aea create my_thermometer_client
cd my_thermometer_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/thermometer_client:0.1.0
aea install
```

Additionally, create the private key for the thermometer client AEA.
```bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `my_thermometer_aea/aea-config.yaml` and
`my_thermometer_client/aea-config.yaml`, replace `ledger_apis: []` with the following.

``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Update the skill configs

In the thermometer skill config (`my_thermometer_aea/skills/thermometer/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.
``` bash
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```
An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.thermometer.shared_classes.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer.shared_classes.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.thermometer.shared_classes.strategy.args.is_ledger_tx True --type bool
```

In the thermometer client skill config (`my_thermometer_client/skills/thermometer_client/skill.yaml`) under strategy change the `currency_id` and `ledger_id`.
``` bash
max_buyer_tx_fee: 20000
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```
An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set vendor.fetchai.skills.thermometer_client.shared_classes.strategy.args.max_buyer_tx_fee 10000 --type int
aea config set vendor.fetchai.skills.thermometer_client.shared_classes.strategy.args.currency_id ETH
aea config set vendor.fetchai.skills.thermometer_client.shared_classes.strategy.args.ledger_id ethereum
aea config set vendor.fetchai.skills.thermometer_client.shared_classes.strategy.args.is_ledger_tx True --type bool
```

### Fund the thermometer client AEA

Create some wealth for your thermometer client on the Ethereum Ropsten test net.

Go to the <a href="https://faucet.metamask.io/" target=_blank>MetaMask Faucet</a> and request some test ETH for the account your thermometer
client AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `my_thermometer_client/eth_private_key.txt`.

### Run the AEAs
You can change the end point's address and port by modifying the connection's yaml file (my_thermometer_aea/connection/oef/connection.yaml)

Under config locate :

```bash
addr: ${OEF_ADDR: 127.0.0.1}
```
 and replace it with your ip (The ip of the machine that runs the oef image.)


Run both AEAs, from their respective terminals.
``` bash
aea run --connections fetchai/oef:0.1.0
```
You will see that the AEAs negotiate and then transact using the Ethereum `testnet`.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
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
