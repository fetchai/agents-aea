
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
from aea.configurations.base import PublicId

weather_client_id = PublicId.from_str("fetchai/weather_client:0.19.0")
weather_station_id = PublicId.from_str("fetchai/weather_station:0.18.0")
manager.add_project(weather_client_id)
manager.add_project(weather_station_id)
```

## Adding agent instances

Save the following private keys in the respective files.
``` python
# 72d3149f5689f0749eaec5ebf6dba5deeb1e89b93ae1c58c71fd43dfaa231e87
FET_PRIVATE_KEY_PATH_1 = "fetchai_private_key_1.txt"
# bf529acb2546e13615ef6004c48e393f0638a5dc0c4979631a9a4bc554079f6f
COSMOS_PRIVATE_KEY_PATH_1 = "cosmos_private_key_1.txt"
# 589839ae54b71b8754a7fe96b52045364077c28705a1806b74441debcae16e0a
FET_PRIVATE_KEY_PATH_2 = "fetchai_private_key_2.txt"
# c9b38eff57f678f5ab5304447997351edb08eceb883267fa4ad849074bec07e4
COSMOS_PRIVATE_KEY_PATH_2 = "cosmos_private_key_2.txt"
```

Add the agent instances
``` python
agent_overrides = {
    "private_key_paths": {"fetchai": FET_PRIVATE_KEY_PATH_1},
    "connection_private_key_paths": {"cosmos": COSMOS_PRIVATE_KEY_PATH_1}
}
manager.add_agent(weather_station_id, agent_overrides=agent_overrides)

component_overrides = {
    "name": "p2p_libp2p",
    "author": "fetchai",
    "version": "0.9.0",
    "type": "connection",
    "config": {
        "delegate_uri": "127.0.0.1:11001",
        "entry_peers": ['/dns4/127.0.0.1/tcp/9000/p2p/16Uiu2HAkzgZYyk25XjAhmgXcdMbahrHYi18uuAzHuxPn1KkdmLRw'],
        "local_uri": "127.0.0.1:9001",
        "public_uri": "127.0.0.1:9001",
    }
}
agent_overrides = {
    "private_key_paths": {"fetchai": FET_PRIVATE_KEY_PATH_2},
    "connection_private_key_paths": {"cosmos": COSMOS_PRIVATE_KEY_PATH_2}
}
manager.add_agent(weather_client_id, component_overrides=[component_overrides], agent_overrides=agent_overrides)
```

## Running the agents:

``` python
manager.start_agent(weather_station_id.name)
# wait for ~10 seconds for peer node to go live
manager.start_agent(weather_station_id.name)
```

## Stopping the agents:

``` python
manager.stop_all_agents()
```

## Cleaning up

``` python
manager.stop_manager()
```