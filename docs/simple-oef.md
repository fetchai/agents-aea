# Simple-OEF

This documentation has been produced for the Simple-OEF version `0.2.7`.

## Concepts

The Simple-OEF, or soef, is a **search and discovery** mechanism for **autonomous economic agents**. Agents register with the soef and are then able to conduct searches around them to find other agents that may be able to help. It is a relatively simple implementation focussing on functionality, performance and ease-of-use. As it develops, it will evolve into a full-scale decentralised, multi-dimensional digital world. 

The work-flow is:

* *Find* relevant agents on the soef,
* *Communicate* using the Agent Framework's peer-to-peer network,
* *Negotiate* and then transact on the ledger in order to exchange value for tokens

When an agent registers with the soef, it is issued with a _unique reference_ which is quoted in all subsequent transactions. This way, the soef knows who its talking to. The soef is transaction based, so it does not need a permanent connection to be maintained in order to work with it. If it does not hear from an agent for a period of time, that agent will be timed out and automatically unregistered. This period of time is typically about one hour, but you can see the soef's configuration at:

<a href="http://soef.fetch.ai:9002" target="_blank">http://soef.fetch.ai:9002</a>

Agents identify themselves in a number of ways. These include their address, their given name, their classification and their genus. They can also describe how they "look" in other ways, and specify the services that they provide. 

In order to register, agents _must_ provide a valid address and a given name. The address can be for the Fetch.ai native ledger, the Fetch.ai Cosmos ledger or the ethereum ledger. It is this that uniquely identifies them, and addresses cannot be duplicated or shared. The given name can be anything and it is not used for search filtering. Typically, it can be thought of as a debugging aid or a context. Names could be Alice, Bob or Jim, as well as they could be a flight number, train identity or reference code. They _appear_ in find results, but are not used to find by.

## Describing an Agent

Agents describe themselves in three ways:

1. **Identity**: their address and ledger type along with their given name
2. **Personality pieces**: how they _look_
3. **Service keys**: what they _do_, _sell_ or _want_. 

We cover all of these in this next section. It's important to understand the difference between personality pieces and service keys, as agents only have one appearance, but they can provide many services. Search results can be filtered by a number of both, and wildcards are permitted where relevant.

### Personality Pieces

Agents can have a number of personality peices. These describe how an agent appears, where it is, and other properties such as heading, supported protocols and types of transactions. All personality pieces are optional. 

| Piece               | Description                                                  |
| ------------------- | ------------------------------------------------------------ |
| `genus`             | Coarse type of agent, includes things such as `vehicle`, `building`, `iot`. See the genus table below. |
| `classification`    | An agent's classification, typically in the form `mobility.railway.train`. See note below on classifications. No fixed classifications are specified. Classifications can contain alphanumeric characters, the period, underscore and colon (`_.:`). |
| `architecture` | Agent's architecture. See the architecture table below. Introduced in version `0.1.20`. The vast majority of agents should set this to `agentframework`. |
| `dynamics.moving`   | Boolean, indicates if the agent is moving or not.            |
| `dynamics.heading`  | Indicates the heading of the agent, in radians, with 0.0 pointing due north. |
| `dynamics.position` | Indicates the GPS co-ordinates of the agent as latitude and longitude. |
| `action.buyer`      | Boolean, indicates whether the agent wishes to buy information, i.e., is an agent that requires value from another agent. |
| `action.seller`     | Boolean, indicates whether the agent sells information, i.e., provides value. Value provided can be zero-cost. |

#### Genus list

A genus is a coarse agent class. It is the roughest description of what an agent is, and an easy way of filtering large groups of agents out of searches. The supported genus list is:

| Name        | Description                                                  |
| ----------- | ------------------------------------------------------------ |
| `test` | Agent is a test agent, and should be generally ignored |
| `vehicle`   | Moving objects such as trains, planes and automobiles        |
| `avatar`    | An agent that _represents_ a human being                     |
| `service`   | An agent that provides a service                             |
| `iot`       | An agent that represents an Internet of Things device        |
| `data`      | An agent that represents data                                |
| `furniture` | Small fixed location items such as signs, mobile masts       |
| `building`  | Large fixed location item such as house, railway station, school |
| `buyer`     | Indicates the agent is a buyer _only_ and does not have value to deliver |
| `viewer` |The agent is a view in the world, acting as a "camera" to view content |

The best way to use genus is to pick the *best fit* choice. If there isn't one for you, then do not specify it. If you feel that a high-level genus is missing, please make the suggestion in our Developer Discord (see <a href="https://discord.com/invite/qnYED4hGBc" target="_blank">here</a>). 

#### Architectures

An architecture is a clue to other agents to describe how the agent is built. The vast majority of agents will be built using the Fetch Agent Framework, but in some cases, such as light-weight IoT devices or test/debugging, agents are built otherwise. Architecture offers a way of describing or filtering, as agents with a similar architecture are more likely to be able to communicate with each other in a meaninful way.

| Architecture     | Description                           |
| ---------------- | ------------------------------------- |
| `custom`         | Custom agent architecture             |
| `agentframework` | Built using the Fetch Agent Framework |

#### A note on classifications

There is currently no fixed set of guidelines as to how classifications are used. It is expected that agent builders will converge on a set of standards, and as those become clearer, they will be documented as "by convention" classification uses. Here are some examples of classifications in use:

```bash
mobility.railway.station
mobility.railway.train
mobility.road.taxi
infrastructure.road.sign
```

When filtering by classifications, the `*` wildcard can be used to, for example, capture all mobility related agents with a wildcard of `mobility.*`. 

### Service Keys

Agents can have a number of service keys. Service keys are simple key/value pairs that describe the list of services that the agent provides. Whilst personality pieces can be thought of as how an agent _looks_, service keys are what an agent _has_ or _does_. Service keys are user defined and as with personality pieces, currently have no convention for formatting. They are at the agent builder's descretion. As this changes, the documentation will be updated. However, for _buyer_ agents, three suggested keys are:

```bash
buying_genus
buying_architecture
buying_classifications
```

This allows searches to look for potential buyers of classifications, genus or with a compatible architecture. 

## Finding Agents

The soef is designed for **geographic searches** where agents are able to find other agents near to them that are able to provide them with the value that they want, or who might wish to have the value they provide. However, it also allows for **positionless searches** on a single node. Future versions of the soef will support searches across nodes, and dimensional reduction-based fuzzy searches. 

Geographic searches are performed using the  `find_around_me` operation. This allows searches that:

* Are within a certain range in KM
* That have a specified set of personality pieces (with wildcards where applicable)
* That have a specified set of service keys (with wildcards)
* Where chain identifiers match

Positionless searches are performed using the `find_on_this_node` operation. This allows searches that:

* That have a specified set of personality pieces (with wildcards where applicable)
* That have a specified set of service keys (with wildcards)
* Where chain identifiers match

**At least one** filter must be supplied in positionless searches. Positionless searches are not boundless, they are capped at a specific number. The tighter the filters, the less likely that you will be capped. 

Some limits apply to the maximum number of filters, range and returned results. This may vary from soef instance to soef instance. You can see (and parse if required) these by getting the soef status at:

<a href="http://soef.fetch.ai:9002" target="_blank">http://soef.fetch.ai:9002</a>

The soef returns XML that includes information about all found agents. An example of that, unparsed, looks like this:

```xml
<response>
  <success>1</success>
  <total>1</total>
  <capped>0</capped>
  <results>
    <agent name="TrainNumber1234" genus="vehicle" classification="mobility.railway.train" user_context="18:00 to Berlin">
      <identities>
        <identity chain_identifier="fetchai">2h6fi8oCkMz9GCpL7EUYMHjzgdRFGmDP5V4Ls97jZpzjg523yY</identity>
      </identities>
      <range_in_km>55.7363</range_in_km>
      <location accuracy="3">
        <latitude>52.5</latitude>
        <longitude>0.2</longitude>
      </location>
    </agent>
  </results>
</response>
```

**The `<location>` block is only returned if the agent has set itself to disclose its position in a find.** Likewise, **the `user_context=""` is only returned if enabled**. Normally, the default is not to, and agents will then only return the `<range_in_km>` item. This is because agents may deliver their precise location as part of the value that they deliver, and therefore it would need to be negotiated and potentially paid for. However, sometimes, it is desirable for agents to always deliver their position when found but specify the accuracy. Because of this, the soef supports four levels of accuracy:

| Level     | Accuracy                                            |
| --------- | --------------------------------------------------- |
| `none`    | **Default** do *not* disclose position, range only. |
| `low`     | Rounded to nearest 11km                             |
| `medium`  | Rounded to nearest 1.1km                            |
| `high`    | Rounded to nearest 110 metres                       |
| `maximum` | No rounding: supplied in maximum available detail   |

## Technical Details

For the majority of use cases, the soef will be used from the Agent Framework. As a result, talking to it directly will not be needed. There are some occasions where interacting with the soef directly may be required, and this section documents the API functionality. 

Until version 1.0 (expected in Q3/Q4 2020), some of the security and paid-for-services are not implemented and where they are, generally not enforced. Digital signatures for the sign-on process and unique identity recovery will be implemented, as will encryption on sensitive data transport, for example. Thus the API is likely to change substantially in the coming months, particularly the initial registration process. It is not recommended that you invest in substantial code that talks to the soef directly until after 1.0, and it is always preferred to go through the Agent Framework.

### Registration

Agents register at the `/register` page on the soef. They are expected to provide four pieces of information:

1. An API key
2. A chain identifier, which can be either `fetchai_v1` for the Fetch native network (testnet or mainnet), `fetchai_v2_*` for the Fetch version 2 network or `ethereum` for the ethereum network. See the "Chain identifiers" table below for a complete list of supported chain identifiers. 
3. An address, which must be a valid address for the specified chain identifier
4. A "given name" (see "Concepts", above), which can be anything from Alice to Bob, or a flight number, or any other user-given context. It must not exceed 128 characters. 

If registration is successful, the soef will return a result like this:

```xml
<response>
  <encrypted>0</encrypted>
  <token>0A709D1ED170A3E96C4AC9D014BCAE30</token>
  <page_address>
oef_AEC97453A80FFFF5F11E612594585F611D1728FFCD74BBF4FE915BBBB052
  </page_address>
</response>
```

This indicates success and that the agent is now in the **Lobby**. The lobby is a temporary holding pen where newly registered agents wait until the negotiation is complete. If an agent does not respond and complete its registration within 60 seconds, it is removed from the lobby and registration is cancelled. 

The `<page_address>` is the **unique URL** for the new agent. This must be quoted in all subsequent interactions and is how the soef identifies that specific agent. To complete registration, use the unique URL and specify the parameters:

* `token=` with the token that was returned above and
* `command=acknowledge`

If this works, you will receive a success response:

```xml
<response>
  <success>1</success>
</response>
```

At this point, your agent is now fully registered and can then communicate with the soef. 

Agents that do not contact the soef at least once over a specified interval will be automatically unregistered. The typical setting for this is 60 minutes.

#### Chain identifiers

The soef supports a selection of chain identifiers designed to allow agents to distinguish networks in searches, but also to identify the type of address used for verification purposes. 

| Chain identifier                  | Network                                                      |
| --------------------------------- | ------------------------------------------------------------ |
| `fetchai_v1`                      | Version 1 Fetch.ai network (testnet or mainnet). Versions prior to 0.2 of the soef used `fetchai` for this, which is retained for compatibility. |
| `fetchai_v2_testnet_stable`       | Version 2 Fetch.ai stable testnet, also known as "Agentland". Versions prior to 0.2 of the soef used `fetchai_cosmos` which is retained for compatibility, but deprecated. |
| `fetchai_v2_testnet_incentivised` | Current incentivised testnet. Fetch.ai are running a high-reward sequence of testnets in Q4 2020 and Q1 2021 leading to V2 mainnet. |
| `fetchai_v2_misc`                 | Miscellaneous v2 network. These are temporary or transient testnets where there is a desire to separate the chain ID from other v2 networks. |
| `fetchai_v2_mainnet`              | Fetch.ai v2 mainnet. Not yet active.                         |

### Commands

The soef has a number of commands that can be used to set or update personality pieces, manage service keys, unregister, find other agents and other operations. These commands are specified using the agent's unique URL and a `command=` parameter. There may then be other required and optional parameters for that particular command.

| Command                                 | Details                                                      |
| --------------------------------------- | ------------------------------------------------------------ |
| `unregister`                            | Unregisters the agent from the soef. The unique URL is invalidated and the agent will no longer appear in searches. No parameters. |
| `ping`                                  | Say hello. This is for agents that have been idle for a long period of time and wish to maintain their connection. No parameters. |
| `set_personality_piece`                 | Sets or updates a personality piece. Specify the `piece` (see personality piece table above) and the `value`. For personality pieces with multiple values, such as `dynamics.position`, separate them with the pipe character `|`. |
| `set_service_key`                       | Sets or updates a service key. Specify the `key` and the `value` to assign to it. |
| `remove_service_key`                    | Removes an existing service key. Specify the `key`.          |
| `set_find_position_disclosure_accuracy` | Sets the find disclosure accuracy. See the table in "Finding Agents", above, for the accepted values for the parameter `accuracy`. |
| `find_around_me`                        | Geographic finding of agents around me. This allows various filters, such as personality pieces and service keys, to be specified. See below, as this is more complex. |
| `find_on_this_node`                     | Positionless finding of agents on this node. Various filters such as personality pieces and service keys can narrow the search. See below for more information. |
| `set_position`                          | This is a direct internal mapping to `set_personality_piece` with a piece of `dynamics.position`. It existed in the earliest versions of the soef and remains as a short-cut. It expects `longitude` and `latitude` as parameters. |
| `set_declared_name`                     | This allows an agent's declared name to be changed after registration. It takes one parameter, `name`, to specify the replacement name. Names cannot exceed 128 characters and must not contain illegal characters. |
| `set_user_context`                      | Sets an __optional__ user-context for an agent to what is specified in the `value` parameter. This can be optionally disclosed in `find_around_me` if enabled. See `set_disclose_user_context`, below. The user context must not contain illegal characters and is limited to 160 maximum. |
| `set_disclose_user_context`             | If the `disclose` parameter is set to `true`, the optional user context is disclosed if it has been set. Default is `false`. |

#### Find commands in detail

`find_around_me` and `find_on_this_node` are the big commands. Ultimately, they will cost a small amount of tokens to use, depending on the size of the request, as it involves the most computing time. This provides an incentive for soef operators to maintain soef nodes that correspond to subject areas, geographic areas or both. The command has a number of parameters specifying the filtering required. For `find_around_me`, the `range_in_km` is *required*. This cannot exceed a certain range, typically between 50 and 75km. This, and other configuration items, are available on the soef's configuration page. There are other parameters that are optional, although for `find_on_this_node` at least one `ppfilter` or `skfilter` must be specified. The parameters are:

| Parameter           | Use                                                          |
| ------------------- | ------------------------------------------------------------ |
| `chains_must_match` | Boolean. Must be `true` or `false`. Default is `false`. If specified, this ensures that any agents returned in the search will have the same chain identifier as you. |
| `ppfilter`          | Specify a personality piece filter. Multiple `ppfilter`s can be specified. Example use is: `ppfilter=dynamics.moving,true`. Wildcards can be used where relevant, e.g.: `ppfilter=classification,mobility*` will match all classifications that *start* with `mobility`, whereas `ppfilter=classification,*mobility*` will match all classifications with `mobility` anywhere in it. |
| `skfilter`          | Specify a service key filter. Multiple `skfilter`s can be specified. Example use is: `skfilter=fruit,peach` which will require any returned results to have a service key of `fruit` and a value of `peach`. Wildcards can be specified, so `skfilter=fruit,pea*` will match any agent with a service key of `fruit` that starts `pea`, so `pear` and `peach` would match. |

#### SK Filters: filter modes

The `skfilter` parameter for `find_around_me` also supports a _mode_. Four modes are supported:

| Mode string | Description                                    |
| ----------- | ---------------------------------------------- |
| PS          | Key must be present, and success is required   |
| PF          | Key must be present, and failure is required   |
| OS          | Only match if present, and success is required |
| OF          | Only match if present, and failure is required |

For example:

```
command=find_around_me&range_in_km=50&skfilter=type,fruit,PS&skfilter=size,large,OF
```

In this example, the key `type` must be present, and it must match to `fruit`. If the `size` key is present, and it is set to `large`, then do not match. I.e., return everything that's a fruit within 50km except where the size is large. 

## Further information

You can find further information, or talk to us, in the #agents channel on our official developer Discord server, which you can access 
<a href="https://discord.com/invite/qnYED4hGBc" target="_blank">here</a>.

We welcome your feedback and strive to deliver the best decentralised search and discovery service for agents that is possible. There are many upcoming features, including the operation incentive mechanisms, additional security and encryption, active searches (where results happen without `find_around_me` being issued), non-geographic searches across one and many soef nodes and dimensional-reduction based approximate searches. 

[Docs: issue 13, 0.2.7, 05-Nov-2020, TWS]

