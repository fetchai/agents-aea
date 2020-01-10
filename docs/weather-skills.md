The AEA weather skills demonstrate an interaction between two AEAs.

* The provider of weather data (the weather station).
* The seller of weather data (the weather client).

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.


### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo instructions 1: no ledger payment

The AEAs negotiate and then transfer the data. No payment takes place. This demo serves as a demonstration of the negotiation steps.

### Create the weather station AEA
In the root directory, create the weather station AEA.
``` bash
aea create my_weather_station
```


### Add the oef connection and the weather station skill 
``` bash
cd my_weather_station
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_station:0.1.0
aea install
```


### Run the weather station AEA
``` bash
aea run --connections oef
```


### Create the weather client AEA
In a new terminal window, return to the root directory and create the weather client AEA.
``` bash
aea create my_weather_client
```


### Add the oef connection and the weather client skill 
``` bash
cd my_weather_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_client:0.1.0
aea install
```


### Run the weather client AEA
``` bash
aea run --connections oef
```


### Observe the logs of both AEAs

<center>![Weather station logs](assets/weather-station-logs.png)</center>

<center>![Weather client logs](assets/weather-client-logs.png)</center>

To stop an agent use `CTRL + C`.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the car park agent to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Weather_AEA
    
        activate Client_AEA
        activate Search
        activate Weather_AEA
        
        Weather_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Weather_AEA: call_for_proposal
        Weather_AEA->>Client_AEA: propose
        Client_AEA->>Weather_AEA: accept
        Weather_AEA->>Client_AEA: match_accept
        Client_AEA->>Weather_AEA: Inform funds transfered 
        Weather_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Weather_AEA
    
</div>
Note that the client informs the weather station that funds have been transfereed, but in this example no funds actually get transfered.

## Demo instructions 2: Fetch.ai ledger payment

A demo to run the same scenario but with a true ledger transaction on Fetch.ai `testnet`. This demo assumes the weather client trusts the weather station to send the weather data upon successful payment.

### Create the weather station (ledger version)

Create the AEA that will provide weather measurements.

``` bash
aea create my_weather_station
cd my_weather_station
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_station:0.1.0
aea install
```

### Create the weather client (ledger version)

In another terminal, create the AEA that will query the weather station.

``` bash
aea create my_weather_client
cd my_weather_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_client:0.1.0
aea install
```

Additionally, create the private key for the weather client AEA.
```bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

### Update the AEA configs

Both in `my_weather_station/aea-config.yaml` and
`my_weather_client/aea-config.yaml`, replace `ledger_apis: {}` with the following.

``` yaml
ledger_apis:
  fetchai:
    address: alpha.fetch-ai.com
    port: 80
```

### Fund the weather client AEA

Create some wealth for your weather client on the Fetch.ai `testnet`. (It takes a while).
``` bash
cd ..
python scripts/fetchai_wealth_generation.py --private-key my_weather_client/fet_private_key.txt --amount 10000000 --addr alpha.fetch-ai.com --port 80
cd my_weather_client
```

### Update the skill configs

Tell the weather client skill of the weather client that we want to settle the transaction on the ledger:
``` bash
aea config set skills.weather_client.shared_classes.strategy.args.is_ledger_tx True
```

Similarly, for the weather station skill of the weather station:
``` bash
aea config set skills.weather_station.shared_classes.strategy.args.is_ledger_tx True
```

### Run the AEAs

Run both AEAs from their respective terminals.
``` bash
aea run --connections oef
```

You will see that the AEAs negotiate and then transact using the Fetch.ai `testnet`.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

## Demo instructions 3: Ethereum ledger payment

A demo to run the same scenario but with a true ledger transaction on the Ethereum Ropsten `testnet`. This demo assumes the weather client trusts the weather station to send the weather data upon successful payment.

### Create the weather station (ledger version)

Create the AEA that will provide weather measurements.

``` bash
aea create my_weather_station
cd my_weather_station
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_station:0.1.0
aea install
```

### Create the weather client (ledger version)

In another terminal, create the AEA that will query the weather station.

``` bash
aea create my_weather_client
cd my_weather_client
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/weather_client:0.1.0
aea install
```

Additionally, create the private key for the weather client AEA.
```bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `my_weather_station/aea-config.yaml` and
`my_weather_client/aea-config.yaml`, replace `ledger_apis: []` with the following.

``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
```

### Update the skill configs

In the weather station skill config (`my_weather_station/skills/weather_station/skill.yaml`) under strategy, amend the `currency_id` and `ledger_id` as follows.
``` bash
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```
An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set skills.weather_station.shared_classes.strategy.args.currency_id ETH
aea config set skills.weather_station.shared_classes.strategy.args.ledger_id ethereum
aea config set skills.weather_station.shared_classes.strategy.args.is_ledger_tx True
```


In the weather client skill config (`my_weather_client/skills/weather_client/skill.yaml`) under strategy change the `currency_id` and `ledger_id`.
``` bash
max_buyer_tx_fee: 20000
currency_id: 'ETH'
ledger_id: 'ethereum'
is_ledger_tx: True
```
An other way to update the skill config is via the `aea config get/set` command.
``` bash
aea config set skills.weather_client.shared_classes.strategy.args.max_buyer_tx_fee 10000
aea config set skills.weather_client.shared_classes.strategy.args.currency_id ETH
aea config set skills.weather_client.shared_classes.strategy.args.ledger_id ethereum
aea config set skills.weather_client.shared_classes.strategy.args.is_ledger_tx True
```

### Fund the weather client AEA

Create some wealth for your weather client on the Ethereum Ropsten test net.

Go to the <a href="https://faucet.metamask.io/" target=_blank>MetaMask Faucet</a> and request some test ETH for the account your weather client AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `my_weather_client/eth_private_key.txt`.

### Run the AEAs

Run both AEAs, from their respective terminals.
``` bash
aea run --connections oef
```
You will see that the AEAs negotiate and then transact using the Ethereum `testnet`.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the weather station agent to the client. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Client_AEA
        participant Weather_AEA
        participant Blockchain
    
        activate Client_AEA
        activate Search
        activate Weather_AEA
        activate Blockchain
        
        Weather_AEA->>Search: register_service
        Client_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Client_AEA->>Weather_AEA: call_for_proposal
        Weather_AEA->>Client_AEA: propose
        Client_AEA->>Weather_AEA: accept
        Weather_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Weather_AEA: send_transaction_hash
        Weather_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate Search
        deactivate Weather_AEA
        deactivate Blockchain
       
</div>
