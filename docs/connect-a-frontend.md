This page lays out two options for connecting a front-end to an AEA. The following diagram illustrates these two options.

<img src="../assets/http-integration.jpg" alt="How to connect front-end to your AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

## Case 1
The first option is to create a `HTTP Server` connection that handles incoming requests from a REST API. In this scenario, the REST API communicates with the AEA and requests are handled by the `HTTP Server` connection package. The REST API should send CRUD requests to the `HTTP Server` connection (`fetchai/http_server:0.22.0`) which translates these into Envelopes to be consumed by the correct skill.

## Case 2
The second option is to create a front-end comprising a stand-alone `Multiplexer` with a `P2P` connection (`fetchai/p2p_libp2p:0.25.0`). In this scenario the <a href="../acn">Agent Communication Network</a> can be used to send Envelopes from the AEA to the front-end.