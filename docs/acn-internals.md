
The aim of this document is to describe at a high-level
the main implementation of the Agent Communication Network (ACN).

This documentation page is structured as follows:
TODO

## Messages and Data Structures

At the foundation of the ACN there is the _ACN protocol_.
The protocol messages and the reply structure are generated from this 
<a href="https://github.com/fetchai/agents-aea/blob/develop/libs/go/libp2p_node/protocols/acn/v1_0_0/acn.yaml" target="_blank">protocol specification</a>,
using the <a href="../protocol-generator" target="_blank">protocol generator</a>.
Therefore, it uses <a href="https://developers.google.com/protocol-buffers" target="_blank">Protocol Buffers</a>
as a serialization format,
and the definition of the data structures involved is defined in this
<a href="https://github.com/fetchai/agents-aea/blob/develop/libs/go/libp2p_node/protocols/acn/v1_0_0/acn.proto" target="_blank">`.proto` file</a>.

To know more about the protocol generator, refer to the relevant
section of the documentation:
<a href="../protocol-generator" target="_blank">Protocol Generator</a>.

### Agent Record

An _agent record_ is a data structure containing information about an
agent and its Proof-of-Representation (PoR) to be used by a peer for other peers.
This data structure is used as a payload in other ACN messages (see below).

The `AgentRecord` data structure contains the following fields:

- `service_id`: a string describing the service identifier.
- `ledger_id`: a string. It is the identifier of the ledger 
    this agent record is associated to.
    Currently, the allowed values are:
    - `fetchai`, the identifier for the Fetch.AI ledger;
    - `ethereum`, the identifier for the Ethereum ledger;
    - `cosmos`, the identifier for the Cosmos ledger;
- `address`: a string. It is the public key of a public-private key pair.
    It is used as an identifier for routing purposes.
- `public_key`: a string. The representative's public key. Used in case of (PoR).
- `peer_public_key`: a string. The public key of the peer.
- `signature`: a string. The signature for PoR.
- `not_before`: a string. Specify the lower bound for certificate validity.
    If it is a string, it must follow the format: `YYYY-MM-DD`. It will be interpreted as time zone UTC-0
- `not_after`: a string. Specify the upper bound for certificate validity. 
    If it is a string, it must follow the format: `YYYY-MM-DD`. It will be interpreted as time zone UTC-0.


### ACN Message

Entities in the ACN (i.e. either agents or peers) exchange _ACN messages_.
An ACN message contains a `payload` field,
which is the actual content of the message.

There are different types of payloads:

- `Status`
- `Register`
- `LookupRequest`
- `LookupResponse`
- `AeaEnvelope`

### Status

The `Status` payload is used as a response message to inform 
the sender about the handling of certain requests.
The payload contains:

- the `status_code`, a positive integer among the ones in the 
  <a href="https://github.com/fetchai/agents-aea/blob/develop/libs/go/libp2p_node/protocols/acn/v1_0_0/acn.proto" target="_blank">Protobuf file</a>.
- a list of error messages (string).

A status code `0`, identified as `SUCCESS`, 
means that the request has been processed successfully.
Status codes greater than `0` can be:

- Generic errors: errors that occur under generic circumstances.

    - `ERROR_UNSUPPORTED_VERSION`, with integer value `1`: the receiver of the message
         does not support the protocol version of the sender;
    - `ERROR_UNEXPECTED_PAYLOAD`, with integer value `2`: the payload could not be
         deserialised on the receiver side;
    - `ERROR_GENERIC`, with integer value `3`: an internal error;
    - `ERROR_SERIALIZATION`, with integer value `4`: a serialization error occurred
         on the receiving end;

- Register errors: errors that occur during agent registration operations in the ACN. 

    - `ERROR_WRONG_AGENT_ADDRESS`, with integer value `10`:
         the PoR by a peer from another peer does not match the destination address of
         the envelope to be routed by the receiving peer.
    - `ERROR_WRONG_PUBLIC_KEY`, with integer value `11`: the
         representative peer public key does not match the one in the agent record;
    - `ERROR_INVALID_PROOF`, with integer value `12`: the signature is invalid;
    - `ERROR_UNSUPPORTED_LEDGER`, with integer value `13`: the ledger of the PoR is not supported by the peer;

- Lookup and delivery errors: errors that occur during lookup to the DHT and envelope delivery operations in the ACN.
  
    - `ERROR_UNKNOWN_AGENT_ADDRESS`, with integer value `20`: the requested agent address has not been found in the local DHT of the peer;
    - `ERROR_AGENT_NOT_READY`, with integer value `21`: the agent is not ready for envelope delivery.


### Register

The `Register` payload is used to request a peer to register an agent among his known ones.
The payload contains the field `record`, which is an instance of `AgentRecord`.

### LookupRequest

The `LookupRequest` payload is sent between peer to look-up addresses in the Distributed Hash Table (DHT).
It contains the agent address (a string) that the sender needs to correctly route an envelope.

### LookupResponse

The `LookupResponse` payload is the response sent by a peer that received a `LookupRequest`.
It contains the `AgentRecord` associated to the requested address.

### AeaEnvelope

The `AeaEnvelope` payload contains the envelope sent by an agent and to be delivered to another agent.
It contains:

- `envelope`: the envelope to be forwarded, in byte representation;
- an `AgentRecord` (see above).

## Overview of ACN 

TODO

## Joining the ACN network

When an ACN peer wants to join the network, it has
to start from a list of _bootstrap peers_, i.e.
a list of ACN peers to connect with (at least one).

Each node handles four different types of <a href="https://docs.libp2p.io/concepts/stream-multiplexing/" target="_blank">libp2p streams</a>:

- the _notification stream_, identified by the URI `/aea-notif/`:
  this stream is used by new peers to notify their existence to
- the _address stream_, identified by the URI `/aea-address/`:
  used to send look-up requests and look-up responses;
- the _envelope stream_, identified by the URI `/aea/`:
  used to forward and to receive ACN envelopes;
- the _register relay stream_, identified by the URI `/aea-register/`:
  this is to receive messages from clients that want to register their agents addresses;
  this peer, and then it can register their addresses.

To begin with, the node process initializes
the transport connections with the bootstrap peers,
the local copy of the Kademlia Distributed
Hash Table (DHT), 
the persistent storage for agent records,
and performs other non-functional operations 
like setting up the <a href="https://prometheus.io/" target="_blank"> Prometheus monitoring system</a>.
Optionally, can also start listening for relay connections
and delegate connections.

Then, it sets up the notification stream and notifies the bootstrap peers (if any).

<div class="mermaid">
    sequenceDiagram
        participant Peer1
        participant Peer2
        participant Peer3
        note over Peer1: notify<br/>bootstrap peers
        Peer1->>Peer2: notify
        Peer2->>Peer2: wait until notifying peer <br/>added to DHT
        activate Peer2
        Peer1->>Peer3: notify
        Peer3->>Peer3: wait until notifying peer <br/>added to DHT
        activate Peer3
        note over Peer2,Peer3: Peer1 registered to DHT
        deactivate Peer2
        deactivate Peer3
        loop for each local/relay/delegate address 
            Peer1->>Peer1: compute CID from address
            Peer1->>Peer2: register address
            Peer1->>Peer3: register address
        end
        note over Peer1: set up:<br/>- address stream<br/>- envelope stream<br/>- register relay stream
</div>

## Relay connections

If the ACN node is configured to run the relay service,
it sets up the register relay stream, waiting for registration
requests.

The following diagram shows an example of the message exchanged
during a registration request:

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer
        Agent->>Peer: Register
        alt decoding error of ACN message
            Peer->>Agent: Status(ERROR_SERIALIZATION)
        else wrong payload
            Peer->>Agent: Status(ERROR_UNEXPECTED_PAYLOAD)
        else PoR check fails
            alt wrong agent address
                Peer->>Agent: Status(ERROR_WRONG_AGENT_ADDRESS)
            else unsupported ledger
                Peer->>Agent: Status(ERROR_UNSUPPORTED_LEDGER)
            else agent address and public key don't match
                Peer->>Agent: Status(ERROR_WRONG_AGENT_ADDRESS)
            else invalid proof
                Peer->>Agent: Status(ERROR_INVALID_PROOF)
            end
        else PoR check succeeds
            Peer->>Agent: Status(SUCCESS)
            note over Peer: announce agent address<br/>to other peers
        end
</div>

## Delegate connections

If the ACN node is configured to run the delegate service,
it start listening from a TCP socket at a configurable URI.

The following diagram shows an example of the message exchanged
during a registration request:

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer
        Agent->>Peer: Register (via TCP)
        alt decoding error of ACN message
            Peer->>Agent: Status(ERROR_SERIALIZATION)
        else wrong payload
            Peer->>Agent: Status(ERROR_UNEXPECTED_PAYLOAD)
        else PoR check fails
            alt wrong agent address
                Peer->>Agent: Status(ERROR_WRONG_AGENT_ADDRESS)
            else unsupported ledger
                Peer->>Agent: Status(ERROR_UNSUPPORTED_LEDGER)
            else agent address and public key don't match
                Peer->>Agent: Status(ERROR_WRONG_AGENT_ADDRESS)
            else invalid proof
                Peer->>Agent: Status(ERROR_INVALID_PROOF)
            end
        else PoR check succeeds
            Peer->>Agent: Status(SUCCESS)
            note over Peer: announce agent<br/>address to<br/>other peers
            Peer->>Peer: wait data from socket 
            activate Peer
            deactivate Peer
        end
</div>

## ACN transport

In the following sections, we describe the main three steps of the routing
of an envelope through the ACN:

- _ACN entrance_: when an envelope sent by an agent enters 
  the peer-to-peer network via the peer the agent is connected to
  i.e. agent-to-peer communication;
- _ACN routing_: when an envelope gets routed through the peer-to-peer network,
  i.e. peer-to-peer communication;
- _ACN exit_: when an envelope gets delivered to the receiving agent
  through its representative peer, i.e. peer-to-agent communication.
  

### ACN Envelope Entrance: Agent -> Peer

In this section, we will describe the interaction protocols between agents and peers 
for the messages sent by the agent to the ACN network.

The following diagram explains the exchange of messages on entering an envelope in the ACN.

In the case of _direct connection_, 
`Agent` is a Python process, whereas `Peer` is in a separate (Golang) process.
The logic of the Python Agent client is implemented in 
the [AEA connection `fetchai/p2p_libp2p`](https://github.com/fetchai/agents-aea/tree/main/packages/fetchai/connections/p2p_libp2p).
The communication between `Agent` and `Peer` is done through 
an OS pipe for Inter-Process Communication (IPC) between the AEA's process and the libp2p node process;
then, the message gets enqueued to an output queue by an input coroutine.
Finally, the envelope ends up in an output queue, 
which is processed by an output coroutine and routed to the next peer.

In the case of _delegate connection_, 
the message exchange is very similar; however, instead of using 
pipes, the communication is done through the network, i.e. TCP,
with a peer which has the delegate service enabled.
The logic of the `Agent` client connected with a delegate connection
is implemented in 
the [AEA connection `fetchai/p2p_libp2p_client`](https://github.com/fetchai/agents-aea/tree/main/packages/fetchai/connections/p2p_libp2p_client).


<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer
        loop until Status(success) received
            Agent->>Peer: AcnMessage(AeaEnvelope)
            Agent->>Agent: wait
            note left of Agent: Wait until<br/>Status(success)
            alt successful case
                Peer->>Agent: Status(success)
                note over Agent: break loop
            else ack-timeout OR conn-error
                note left of Agent: continue: Try to<br/>resend/reconnect
            else version not supported
                Peer->>Agent: Status(ERROR_UNSUPPORTED_VERSION)
            else error on decoding of ACN message
                Peer->>Agent: Status(SERIALIZATION_ERROR)
            else error on decoding of Envelope payload
                Peer->>Agent: Status(SERIALIZATION_ERROR)
            else the payload cannot be handled
                Peer->>Agent: Status(SERIALIZATION_ERROR)
            end
        end
        note over Peer: route envelope<br/>to next peer
</div>


### ACN Envelope Routing

In this section, we describe the interaction between peers
when it comes to envelope routing.

Assume an envelope arrives from an agent to peer `Peer1`,
i.e. `Peer1` is the first hop 
of the routing.
Let `Agent` be the local agent directly connected
to `Peer1`, `Peer2` a direct peer
of peer `Peer1`.

When the envelope is leaving `Peer1`,
we may have different scenario:

1) In case of direct connection,
   and the field `sender` of the envelope
   is not the local agent address: 
   the message is considered invalid, and it is dropped. 

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer1
        participant Peer2
        Agent->>Peer1: AeaEnvelope
        alt envelope sender not registered locally
            note over Peer1: stop, log error
        end
</div>

2) the `target` of the envelope is 
   the local agent connected to the peer:
   the envelope is routed to the local agent.

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer1
        participant Peer2
        Agent->>Peer1: AeaEnvelope
        alt target == peer1.my_agent
            note over Peer1: envelope destinated<br/> to local agent,<br/> not routing
            loop agent not ready
                note over Peer1: sleep for 100ms
            end
            Peer1->>Agent: AeaEnvelope
            Agent->>Peer1: Status(Success)
        end
</div>

3) the `target` is a delegate client.
   Send the envelope via TCP.

<div class="mermaid">
    sequenceDiagram
        participant Delegate
        participant Peer1
        participant Peer2
        Delegate->>Peer1: AeaEnvelope
        alt destination is a delegate
            note over Peer1: send envelope<br/> to delegate via TCP
            Peer1->>Delegate: AeaEnvelope
            Delegate->>Peer1: Status(Success)
        end
</div>

4) Otherwise, look up the local DHT.
  If an entry is found, use it;
   otherwise, send a look-up request
   to connected peers.

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer1
        participant Peer2
        Agent->>Peer1: AeaEnvelope
        alt address found in DHT
            note over Peer1: destination is a<br/>relay client
        else lookup address in DHT
            note over Peer1: send lookup request<br/> to all peers
            Peer1->>Peer2: LookupRequest
            alt generic error
                Peer2->>Peer1: Status(GENERIC_ERROR)
            else look-up response
                Peer2->>Peer1: LookupResponse
                note over Peer1: Check PoR
            else not found
                Peer2->>Peer1:Status(UNKNOWN_AGENT_ADDRESS)
            end
        end
        note over Peer1,Peer2: Now Peer1 knows the contact peer<br/>is PeerX
</div>

In particular, when a peer receives a LookupRequest message,
it does the following:


<div class="mermaid">
    sequenceDiagram
        participant Peer1
        participant Peer2
        Peer1->>Peer2: LookupRequest
        alt error
            Peer2->>Peer1: Status(Error)
        else local agent/relay/delegate
            note over Peer2: requested address is<br/>a local agent<br/>OR<br/>requested address is<br/>in my relay clients<br/>OR<br/>requested address is<br/>in my delegate clients
            Peer2->>Peer1: LookupResponse
            note over Peer1: Check PoR
        else not found locally
            note over Peer2: send lookup request<br/>to other peers...
            alt found
                Peer2->>Peer1: LookupResponse
                note over Peer1: Check PoR
            else not found
                Peer2->>Peer1:Status(UNKNOWN_AGENT_ADDRESS)
            end
        end
</div>

Let `Peer3` the contact peer of the recipient of the envelope. 
The following diagram shows how the contact peer of the 
envelope recipient handles the incoming envelope:

<div class="mermaid">
    sequenceDiagram
        participant Peer1
        participant Peer3
        Peer1->>Peer3: AeaEnvelope
        alt decoding error of ACN message
            Peer3->>Peer1: Status(ERROR_SERIALIZATION)
        else unexpected payload
            Peer3->>Peer1: Status(ERROR_UNEXPECTED_PAYLOAD)
        else decoding error of envelope payload
            Peer3->>Peer1: Status(ERROR_SERIALIZATION)        
        else PoR check fails
            alt wrong agent address
                Peer3->>Peer1: Status(ERROR_WRONG_AGENT_ADDRESS)
            else unsupported ledger
                Peer3->>Peer1: Status(ERROR_UNSUPPORTED_LEDGER)
            else agent address and public key don't match
                Peer3->>Peer1: Status(ERROR_WRONG_AGENT_ADDRESS)
            else invalid proof
                Peer3->>Peer1: Status(ERROR_INVALID_PROOF)
            end
        else PoR check succeeds
            alt target is delegate, not ready
                Peer3->>Peer1: Status(ERROR_AGENT_NOT_READY)
            else exists delegate, ready
                note over Peer3: forward envelope via<br/>delegate connection
                Peer3->>Peer1: Status(SUCCESS)
            else target is local agent, not ready
                Peer3->>Peer1: Status(ERROR_AGENT_NOT_READY)
            else target is local agent, ready
                note over Peer3: forward envelope via<br/>direct connection
                Peer3->>Peer1: Status(SUCCESS)
            else agent does not exist
                Peer3->>Peer1: Status(ERROR_UNKNOWN_AGENT_ADDRESS)
            end
        end
</div>

### ACN Envelope Exit: Peer -> Agent

The following diagram explains the exchange of messages on exiting an envelope in the ACN.

The same message exchange is done 
both in the case of direct connection and
delegate connection,
similarly for what has been described for the envelope entrance
<a href="#acn-envelope-entrance-agent-peer">(see above)</a>.

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant Peer
        Peer->>Agent: AeaEnvelope
        alt successful case
            Agent->>Peer: Status(success)
        else ack-timeout OR conn-error
            note left of Peer: do nothing
        else error on decoding of ACN message
            Agent->>Peer: Status(GENERIC_ERROR)
        else error on decoding of Envelope payload
            Agent->>Peer: Status(GENERIC_ERROR)
        else wrong payload
            Agent->>Peer: Status(GENERIC_ERROR)
        end
</div>


## Known issues and limitations

In this section, we provide a list of known issues
and limitations of the current implementation
of the ACN, considering both the ACN nodes (written in Golang)
and the AEA connections, for the Python AEA framework, to interact with them.

### Delegate client on client disconnection/reconnection

In case of disconnection/reconnection, delegate client record will be removed.
This can cause two problems: either the delegate client is not found, 
or connection is closed during the send operation.

Possible solutions:
- Create more complicated structure for clients storage;
- Keep the delegate client record for longer; 
- Clean up the record by timeout, per client queues.

Code references:

- record removed: <a href="https://github.com/fetchai/agents-aea/blob/1db1720081969bcec1be5a2000ca176475d2b487/libs/go/libp2p_node/dht/dhtpeer/dhtpeer.go#L864" target="_blank">https://github.com/fetchai/agents-aea/blob/1db1720081969bcec1be5a2000ca176475d2b487/libs/go/libp2p_node/dht/dhtpeer/dhtpeer.go#L864</a>
- send code: <a href="https://github.com/fetchai/agents-aea/blob/1db1720081969bcec1be5a2000ca176475d2b487/libs/go/libp2p_node/dht/dhtpeer/dhtpeer.go#L955" target="_blank">https://github.com/fetchai/agents-aea/blob/1db1720081969bcec1be5a2000ca176475d2b487/libs/go/libp2p_node/dht/dhtpeer/dhtpeer.go#L955</a>


### Golang Node <> Python Client `libp2p` connection

In case of connection between the Golang side (i.e. ACN node) 
and the Python side (i.e. the `libp2p` AEA connection) is broken, 
there is no reconnection attempt.
The Golang side connect to the Python server opened, 
but if the connection is broken Golang can try to reconnect; 
however, the Python side does not know about this and will restart
the node completely.

Possible solutions: the problem requires updates on both sides and assume possible timeouts on broken connection.
If connection is broken, the Python side awaits for reconnection from Golang side, 
and restart node completely after timeout.

### What a peer should do if it receives an acknowledgment with an error?

If an ACN response is the `Status` with error code different from `SUCCESS`,
the forwarding to other peers is not repeated. 

A possible solution is to resend the message; however,
not clear why it should help in case of healthy connection,
how many times the sender should retry, and how it would help.

Discussion on GitHub: 
<a href="https://github.com/fetchai/agents-aea/pull/2509#discussion_r642628983" target="_blank">https://github.com/fetchai/agents-aea/pull/2509#discussion_r642628983</a>
