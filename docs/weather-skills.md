The AEA weather skill demonstrates the interaction between two AEA agents; one as the provider of weather data, the other as the seller of weather data.


## Prerequisites

Make sure you have the latest `aea` version.

``` bash
aea --version
```

If not, update with the following.

``` bash
pip install aea[all] --force --no-cache-dir
```

## Demo instructions

Follow the Preliminaries and Installation instructions <a href="../quickstart" target=_blank>here</a>.


Download the packages and scripts directories.
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/packages
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
```


### Launch the OEF Node:
In a separate terminal, launch an OEF node locally:
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

### Create the weather station agent:
In the root directory, create the weather station agent.
``` bash
aea create my_weather_station
```


### Add the weather station skill 
``` bash
cd my_weather_station
aea add skill weather_station
```


### Run the weather station agent

``` bash
aea run
```


### Create the weather client agent
Return to the root directory, and create the weather client agent.
``` bash
aea create my_weather_client
```


### Add the weather client skill 
``` bash
cd my_weather_client
aea add skill weather_client
```


### Run the weather client agent

``` bash
aea run
```


### Observe the logs of both agents:



### Delete the agents

When you're done, you can go up a level and delete the agents.

``` bash
cd ..
aea delete my_weather_station
aea delete my_weather_client
```

<br/>
