# Weather client

A guide to create an AEA with the gym_skill.

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
