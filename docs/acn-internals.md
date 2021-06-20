
The aim of this document is to describe at a high-level
the main implementation of the Agent Communication Network (ACN).

## Introduction

The ACN protocol implements transmission control over the ACN.
The message serialization is based on 
<a href="https://developers.google.com/protocol-buffers" target="_blank">Protocol Buffers</a>.
and the definition of the data structures involved is defined
<a href="https://github.com/fetchai/agents-aea/blob/develop/libs/go/libp2p_node/acn/acn_message.proto" target="_blank">here</a>.

## Messages and Data Structures

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
  <a href="https://github.com/fetchai/agents-aea/blob/develop/libs/go/libp2p_node/acn/acn_message.proto" target="_blank">Protobuf file</a>.
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

### AeaEnvelope

The `AeaEnvelope` payload contains the envelope sent by an agent and to be delivered to another agent.
It contains:

- `envelope`: the envelope to be forwarded, in byte representation;
- an `AgentRecord` (see above).


## ACN with direct connection

In the following sections, we describe the main three steps of the routing
of an envelope through the ACN:

- _ACN entrance_: when an envelope sent by an agent enters 
  the peer-to-peer network via the peer the agent is connected to
  i.e. agent-to-peer communication;
- _ACN middle_: when an envelope gets routed through the peer-to-peer network,
  i.e. peer-to-peer communication;
- _ACN exit_: when an envelope gets delivered to the receiving agent
  through its representative peer, i.e. peer-to-agent communication.
  

### ACN Entrance

In this section, we will describe the interaction protocols between agents and peers 
for the messages sent by the agent to the ACN network.

#### Envelope entrance: Agent -> AgentApi -> DHTPeer (direct connection)

The following diagram explains the exchange of messages on entering an envelope in the ACN.
Agent is a Python process, whereas AgentApi and Peer are in a separate (Golang) process.

<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant DHTPeer
        loop until Status(success) received
            Agent->>DHTPeer: AcnMessage(AeaEnvelope)
            Agent->>Agent: wait
            note left of Agent: Wait until Status(success)
            alt successful case
                DHTPeer->>Agent: Status(success)
                note over Agent: break loop
            else ack-timeout OR conn-error
                note left of Agent: continue (Try to resend/reconnect)
            else version not supported
                DHTPeer->>Agent: Status(ERROR_UNSUPPORTED_VERSION)
            else error on decoding of ACN message
                DHTPeer->>Agent: Status(SERIALIZATION_ERROR)
            else error on decoding of Envelope payload
                DHTPeer->>Agent: Status(SERIALIZATION_ERROR)
            else the payload cannot be handled
                DHTPeer->>Agent: Status(SERIALIZATION_ERROR)
            end
        end
        note over DHTPeer: route envelope to next peer
</div>

An envelope sent via the `fetchai/p2p_libp2p` connection 
by an AEA's skill passes through:

1. the `fetchai/p2p_libp2p` connection; 
2. a pipe for Inter-Process Communication (IPC) between the AEA's process and the libp2p node process, and then
   it gets enqueued to an output queue by an input coroutine;
3. an output queue, which is processed by an output coroutine and routed to the next peer. 


### ACN middle

In this section, we describe the interaction between peers.


<div class="mermaid">
    sequenceDiagram
        participant DHTPeer1
        participant DHTPeer2
        alt envelope sender not registered locally
            note over DHTPeer1: stop, log error
        end
        alt target == peer1.my_agent
            note over DHTPeer1: route envelope destinated to <br/>local agent, not routing
        end

</div>

### ACN Exit

#### Envelope exit: DHTPeer -> AgentApi -> Agent (direct connection)

The following diagram explains the exchange of messages on exiting an envelope in the ACN.
Agent is a Python process, whereas AgentApi and Peer are in a separate (Golang) process.


<div class="mermaid">
    sequenceDiagram
        participant Agent
        participant AgentApi
        participant DHTPeer
        DHTPeer->>AgentApi: AeaEnvelope
        note right of Agent: Put envelope in AgentApi incoming queue
        AgentApi->>Agent: AeaEnvelope
        alt successful case
            Agent->>AgentApi: Status(success)
        else ack-timeout OR conn-error
            note left of AgentApi: do nothing
        else error on decoding of ACN message
            Agent->>AgentApi: Status(generic_error)
            note left of Agent: use DESERIALIZATION_ERROR
        else error on decoding of Envelope payload
            Agent->>AgentApi: Status(generic_error)
            note left of Agent: use DESERIALIZATION_ERROR
        else wrong payload
            Agent->>AgentApi: Status(generic_error)
            note left of Agent: use some custom error code
        end
</div>
