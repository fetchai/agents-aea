You can use the <a href="../simple-oef">SOEF</a> in the agent framework by using the SOEF connection as a package in your agent project.

## Add the SOEF package
Check out the <a href="../cli-commands">CLI guide</a> on details how to add a connection. You will want to add the `fetchai/soef:0.26.0` connection package. 

## Register your agent and its services

### Register agent location
To register your agent's location, you have to send a message in the `fetchai/oef_search:1.0.0` protocol to the SOEF connection.

First, define a data model for location data:
``` python
from aea.helpers.search.models import Attribute, DataModel, Location

AGENT_LOCATION_MODEL = DataModel(
    "location_agent",
    [Attribute("location", Location, True, "The location where the agent is.")],
    "A data model to describe location of an agent.",
)
```
It is important to use this exact data model, as the SOEF connection can only process specific data models.

Second, create a location object:
``` python
from aea.helpers.search.models import Location

agent_location = Location(52.2057092, 2.1183431)
```

Third, construct a service description instance with location and data model:
``` python
from aea.helpers.search.models import Description

service_instance = {"location": agent_location}
service_description = Description(
    service_instance, data_model=AGENT_LOCATION_MODEL
)
```

Finally, construct a message and send it:
``` python
from packages.fetchai.protocols.oef_search.message import OefSearchMessage

message = OefSearchMessage(
    performative=OefSearchMessage.Performative.REGISTER_SERVICE,
    service_description=service_description,
)
```

In case everything is registered OK, you will not receive any message back.

If something goes wrong you will receive an error message with performative `OefSearchMessage.Performative.OEF_ERROR`.

### Register personality pieces

To register personality pieces, you have to use a specific data model:
``` python
from aea.helpers.search.models import Attribute, DataModel, Location

AGENT_PERSONALITY_MODEL = DataModel(
    "personality_agent",
    [
        Attribute("piece", str, True, "The personality piece key."),
        Attribute("value", str, True, "The personality piece value."),
    ],
    "A data model to describe the personality of an agent.",
)
```

An example follows:
``` python
service_instance = {"piece": "genus", "value": "service"}
service_description = Description(
    service_instance, data_model=AGENT_PERSONALITY_MODEL
)
```

### Register services

To set some service key and value you have to use a specific data model:
``` python
SET_SERVICE_KEY_MODEL = DataModel(
    "set_service_key",
    [
        Attribute("key", str, True, "Service key name."),
        Attribute("value", str, True, "Service key value."),
    ],
    "A data model to set service key.",
)
```

An example follows:
``` python
service_instance = {"key": "test", "value": "test"}
service_description = Description(
    service_instance, data_model=SET_SERVICE_KEY_MODEL
)
```

### Remove service key

To remove service key have to use a specific data model:
``` python
REMOVE_SERVICE_KEY_MODEL = DataModel(
    "remove_service_key",
    [Attribute("key", str, True, "Service key name.")],
    "A data model to remove service key.",
)
```

An example follows:
``` python
service_instance = {"key": "test"}
service_description = Description(
    service_instance, data_model=REMOVE_SERVICE_KEY_MODEL
)
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Currently, the soef does not allow for multiple registrations to be combined into a single command.
</div>

## Perform a search

To perform a search for services registered you have to define a search query consisting of constraints. The location constraints is required, personality pieces or services keys constraints are optional.

An example follows:
``` python
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Location,
    Query,
)

radius = 0.1
close_to_my_service = Constraint(
    "location", ConstraintType("distance", (agent_location, radius))
)
personality_filters = [
    Constraint("genus", ConstraintType("==", "vehicle")),
    Constraint(
        "classification", ConstraintType("==", "mobility.railway.train")
    ),
]

service_key_filters = [
    Constraint("test", ConstraintType("==", "test")),
]

closeness_query = Query(
    [close_to_my_service] + personality_filters + service_key_filters
)

message = OefSearchMessage(
    performative=OefSearchMessage.Performative.SEARCH_SERVICES,
    query=closeness_query,
)
```

In case of error you will received a message with `OefSearchMessage.Performative.OEF_ERROR`. In case of successful search you will receive a message with performative `OefSearchMessage.Performative.SEARCH_RESULT` and the list of matched agents addresses.

## Generic command

To send a generic command request to the SOEF use the following (here on the example of setting a declared name):
``` python
import urllib

AGENT_GENERIC_COMMAND_MODEL = DataModel(
    "generic_command",
    [
        Attribute("command", str, True, "Command name to execute."),
        Attribute("parameters", str, False, "Url encoded parameters string."),
    ],
    "A data model to describe the generic soef command.",
)

declared_name = "new_declared_name"
service_description = Description(
    {
        "command": "set_declared_name",
        "parameters": urllib.parse.urlencode({"name": declared_name}),
    },
    data_model=AGENT_GENERIC_COMMAND_MODEL,
)
message = OefSearchMessage(
    performative=OefSearchMessage.Performative.REGISTER_SERVICE,
    service_description=service_description,
)
```