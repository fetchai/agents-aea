
The <a href="../api/manager">`MultiAgentManager`</a> allows managing multiple agent projects programmatically.

## Setup

We intantiate the manager by providing it with the working directory in which to operate and starting it:

``` python
from aea.manager import MultiAgentManager

WORKING_DIR = "."

manager = MultiAgentManager(WORKING_DIR)
manager.start_manager()
```

## Adding projects

We first add a couple of finished AEA project:

``` python
manager.add_project("fetchai/weather_client:0.13.0")
manager.add_project("fetchai/weather_station:0.13.0")
```

## Adding agent instances

``` python
manager.add_agent("fetchai/weather_client:0.13.0")
manager.add_agent("fetchai/weather_station:0.13.0")
```

missing:
- configuring private keys
- configure delayed startup sequence


## Running the agents:

``` python
manager.start_all_agents()
```

## Stopping the agents:

``` python
manager.stop_all_agents()
```

## Cleaning up

``` python
manager.stop_manager()
```