This demo discusses the options we have to connect a front-end to the AEA. The following diagram illustrates the two options we are going to discuss.

<img src="../assets/http-integration.png" alt="How to connect frontend to your AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

## Case 1
The first option we have is to create a `Connection` that will handle the incoming requests from the rest API. In this scenario, the rest API communicates with the AEA and requests are handled by the `HTTP Server` Connection package. The rest API should send CRUD requests to the `HTTP Server` Connection (`fetchai/http_server:0.10.0`) which translates these into Envelopes to be consumed by the correct skill.

## Case 2
The other option we have is to create a stand-alone `Multiplexer` with a `P2P` connection (`fetchai/p2p_libp2p:0.11.0`). In this scenario, the front-end needs to incorporate a Multiplexer with an `P2P` Connection. Then the <a href="../acn">Agent Communication Network</a> can be used to send Envelopes from the AEA to the front-end.