The AEA weather skills demonstrate an interaction between two AEAs.

* The provider of weather data (the weather station).
* The seller of weather data (the weather client).


## Prerequisites

Make sure you have the latest `aea` version.

``` bash
aea --version
```

If not, update with the following.

``` bash
pip install aea[all] --force --no-cache-dir
```

## Demo preliminaries

Follow the Preliminaries and Installation instructions <a href="../quickstart" target=_blank>here</a>.


Download the packages and scripts directories.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
```


## Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo 1: no ledger payment

The AEAs negotiate and then transfer the data. No payment takes place. This demo serves as a demonstration of the negotiation steps.

### Create the weather station AEA
In the root directory, create the weather station AEA.
``` bash
aea create my_weather_station
```


### Add the weather station skill 
``` bash
cd my_weather_station
aea add skill weather_station
```


### Run the weather station AEA
``` bash
aea run
```


### Create the weather client AEA
In a new terminal window, return to the root directory and create the weather client AEA.
``` bash
aea create my_weather_client
```


### Add the weather client skill 
``` bash
cd my_weather_client
aea add skill weather_client
```


### Run the weather client AEA
``` bash
aea run
```


### Observe the logs of both AEAs

<center>![Weather station logs](assets/weather-station-logs.png)</center>

<center>![Weather client logs](assets/weather-client-logs.png)</center>


### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```


## Demo 2: Fetch.ai ledger payment

A demo to run the same scenario but with a true ledger transaction on Fetch.ai `testnet`. This demo assumes the weather client trusts the weather station to send the weather data upon successful payment.

### Create the weather station (ledger version)

Create the AEA that will provide weather measurements.

``` bash
aea create my_weather_station 
cd my_weather_station
aea add skill weather_station_ledger
```

### Create the weather client (ledger version)

In another terminal, create the AEA that will query the weather station.

``` bash
aea create my_weather_client 
cd my_weather_client 
aea add skill weather_client_ledger
```

Additionally, create the private key for the weather client AEA.
```bash
aea generate-key fetchai
```

### Update the AEA configs

Both in `weather_station/aea-config.yaml` and
`weather_client/aea-config.yaml`, replace `ledger_apis: []` with the following.

``` yaml
ledger_apis:
  - ledger_api:
      ledger: fetchai
      addr: alpha.fetch-ai.com
      port: 80
```

### Fund the weather client AEA

Create some wealth for your weather client on the Fetch.ai `testnet`. (It takes a while).
``` bash
cd ..
python scripts/fetchai_wealth_generation.py --private-key weather_client/fet_private_key.txt --amount 10000000 --addr alpha.fetch-ai.com --port 80
cd my_weather_client
```

### Run the AEAs

Run both AEAs from their respective terminals.
``` bash
aea run
```

You will see that the AEAs negotiate and then transact using the Fetch.ai `testnet`.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

## Demo 3: Ethereum ledger payment

A demo to run the same scenario but with a true ledger transaction on the Ethereum Ropsten `testnet`. This demo assumes the weather client trusts the weather station to send the weather data upon successful payment.

### Create the weather station (ledger version)

Create the AEA that will provide weather measurements.

``` bash
aea create my_weather_station 
cd my_weather_station
aea add skill weather_station_ledger
```

### Create the weather client (ledger version)

In another terminal, create the AEA that will query the weather station.

``` bash
aea create my_weather_client 
cd my_weather_client 
aea add skill weather_client_ledger
```

Additionally, create the private key for the weather client AEA.
```bash
aea generate-key ethereum
```

### Update the AEA configs

Both in `weather_station/aea-config.yaml` and
`weather_client/aea-config.yaml`, replace `ledger_apis: []` with the following.

``` yaml
ledger_apis:
  - ledger_api:
      addr: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
      ledger: ethereum
      port: 3
```

### Update the skill configs

In the weather station skill config (`my_weather_station/skills/weather_station_ledger/skill.yaml`) under strategy, amend the `currency_pbk` and `ledger_id` as follows.
``` bash
currency_pbk: 'ETH'
ledger_id: 'ethereum'
```
Amend `ledgers` to the following.
``` bash
ledgers: ['ethereum']
```

In the weather client skill config (`my_weather_client/skills/weather_client_ledger/skill.yaml`) under strategy change the `currency_pbk` and `ledger_id`.
``` bash
max_buyer_tx_fee: 20000
currency_pbk: 'ETH'
ledger_id: 'ethereum'
```
Amend `ledgers` to the following.
``` basgh
ledgers: ['ethereum']
```

### Fund the weather client AEA

Create some wealth for your weather client on the Ethereum Ropsten test net.

Go to the <a href="https://faucet.metamask.io/" target=_blank>MetaMask Faucet</a> and request some test ETH for the account your weather client AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `weather_client/eth_private_key.txt`.

### Run the AEAs

Run both AEAs, from their respective terminals.
``` bash
aea run
```
You will see that the AEAs negotiate and then transact using the Ethereum `testnet`.

### Delete the AEAs

When you're done, go up a level and delete the AEAs.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```


<br/>


