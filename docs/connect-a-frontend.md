This demo discusses the options we have to connect a front-end to the AEA. The following diagram illustrates the two options we are going to discuss.

<center>![How to connect frontend to your AEA](assets/http-integration.png)</center> 

## Case 1
The first option we have is to create a `Connection` that will handle the incoming requests from the rest API. In this scenario, the rest API communicates with the AEA and requests are handled by the `HTTP Server` Connection package. The rest API should send CRUD requests to the `HTTP Server` Connection (`fetchai/http_server:0.3.0`) which translates these into Envelopes to be consumed by the correct skill.

## Case 2
The other option we have is to create a stand-alone `Multiplexer` with an `OEF` connection (`fetchai/oef:0.4.0`). In this scenario, the front-end needs to incorporate a Multiplexer with an `OEF` Connection. Then the [OEF communication node](../oef-ledger) can be used to send Envelopes from the AEA to the front-end.
