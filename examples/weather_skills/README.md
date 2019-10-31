# Weather station and client example

A guide to create two AEAs, one a weather station selling weather data, another a 
purchaser (client) of weather data. This setup assumes the weather client trusts the weather station
to send the data upon successful payment.

## Without ledger

The AEAs negotiate and then transfer the data. No payment takes place.

- Launch the OEF Node (for search and discovery):

      python scripts/oef/launch.py -c ./scripts/oef/launch_config.json

- Create a weather station - the agent that will provide weather measurements:

      aea create weather_station
      cd weather_station
      aea add skill weather_station
      aea run

- In another terminal, create the weather client - the agent that will query the weather station

      aea create weather_client
      cd weather_client
      aea add skill weather_client
      aea run

- Afterwards, clean up:
      
      cd ..
      aea delete weather_station
      aea delete weather_client


## With ledger (Fetch.ai)

The AEAs use the Fetch.ai ledger to settle their trade. 

- Launch the OEF Node (for search and discovery):

      python scripts/oef/launch.py -c ./scripts/oef/launch_config.json

- Create a weather station (ledger version) - the agent that will provide weather measurements:

      aea create weather_station
      cd weather_station
      aea add skill weather_station_ledger

- In another terminal, create the weather client (ledger version) - the agent that will query the weather station

      aea create weather_client
      cd weather_client 
      aea add skill weather_client_ledger

- Generate the private key for the weather client:

      aea generate-key fetchai

- Both in `weather_station/aea-config.yaml` and
`weather_client/aea-config.yaml`, replace `ledger_apis: []` with:
```
ledger_apis:
- ledger_api:
    addr: alpha.fetch-ai.com
    ledger: fetchai
    port: 80
```

- Generate some wealth to your weather client FET address (it takes a while):
```
cd ..
python scripts/fetchai_wealth_generation.py --private-key weather_client/fet_private_key.txt --amount 10000000 --addr alpha.fetch-ai.com --port 80
cd weather_client
```

- Run both agents, from their respective terminals:

      aea run

- Afterwards, clean up:
      
      cd ..
      aea delete weather_station
      aea delete weather_client

## With ledger (Ethereum)

The AEAs use the Ethereum ledger to settle their trade. 

- Follow the first three steps from the previous section.

- Generate the private key for the weather client:

      aea generate-key ethereum

- Both in `weather_station/aea-config.yaml` and
`weather_client/aea-config.yaml`, replace `ledger_apis: []` with:
```
- ledger_api:
    addr: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    ledger: ethereum
    port: 3
```

- In weather station client skill config under strategy change to
```
currency_pbk: 'ETH'
ledger_id: 'ethereum'
```
and under ledgers change to:
```
ledgers: ['ethereum']
```

- Generate some wealth to your weather client ETH address:

Go to Metamask [Faucet](https://faucet.metamask.io) and request some test ETH for the account your AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `weather_client/eth_private_key.txt`.

- Follow the last two stesp from the previous section.
