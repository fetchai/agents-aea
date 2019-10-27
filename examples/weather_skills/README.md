# Weather station and client example

A guide to create two AEAs, one a weather station selling weather data, another a 
purchaser (client) of weather data. The AEAs use the Fetch.ai ledger to settle their 
trade. This setup assumes the weather client trusts the weather station to send the data
upon successful payment.

## Quick start

- Launch the OEF Node:

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


## Using the ledger

To run the same example but with a true ledger transaction,
follow these steps:

- Launch the OEF Node:

      python scripts/oef/launch.py -c ./scripts/oef/launch_config.json

- Create a weather station (ledger version) - the agent that will provide weather measurements:

      aea create weather_station 
      cd weather_station
      aea add skill weather_station_ledger

- In another terminal, create the weather client (ledger version) - the agent that will query the weather station

      aea create weather_client 
      cd weather_client 
      aea add skill weather_client_ledger

- Both in `weather_station/aea-config.yaml` and
`weather_client/aea-config.yaml`, replace `ledger_apis: []` with:
```
ledger_apis:
- ledger_api:
    ledger: fetchai
    addr: alpha.fetch-ai.com
    port: 80
```
- Generate the private key for the weather client:

     aea run

Stop the agent again with `CTRL + C`. You should see that the agent has no balance on Fetch.ai.

- Generate some wealth to your weather client FET address (it takes a while):
```
cd ..
python scripts/fetchai_wealth_generation.py --private-key weather_client/fet_private_key.txt --amount 10000000 --addr alpha.fetch-ai.com --port 80
```

- Run both agents, as in the previous section.