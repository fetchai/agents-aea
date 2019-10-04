# Weather client

A guide to create an AEA with the gym_skill.

## Preliminaries

This demo requires PostgreSQL installed.

If you're on Mac: 

    brew install postgresql

On Debian systems:

    sudo apt-get install postresql
    
For other platforms, please look at the [official page](https://www.postgresql.org/download/).

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
