
The agent communication network (ACN) provides the agents with a system to find each other based on their addresses and communicate.

An agent owner faces the following problem: Given a wallet address, how can my agent whilst maintaining certain guarantees deliver a message to the holder of this address (i.e. another agent)?

The guarantees we would like to have are:

- Reliability: with guarantees on message delivery
- Security: no third-party can tamper with the message
- Authentication: prevent impersonation
- Confidentiality: prevent exposing sensitive information
- Availability: some guarantees about the liveness of the service (tampering detection)

The problem statement and the context impose a number of design constraints:

- Distributed environment: no assumption are placed about the location of the agent, they can be anywhere in the publicly reachable internet
- Decentralized environment: no trusted central authority
- Support for resource-constrained devices

The ACN solves the above problem whilst providing the above guarantees and satisfying the constraints.

## Peers

The ACN is maintained by peers. Peers are not to be equated with agents. They are processes (usually distributed and decentralized) that together maintain the service.

## Distributed hash table

At its core, the ACN comrises of a distributed hash table (DHT). A DHT is similar to a regular hash table in that it stores key-value pairs. However, storage is distributed across multiple machines (peers) with an efficient lookup mechanism. This is enabled by:

- Consistent hashing: assignment
- Structured overlays: (efficient) routing

<img src="../assets/dht.png" alt="DHT" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

For the ACN, we use the DHT to store and maintain association between an agent address and the (network) location of its peer.


## N-tier architecture

To satisfy different resource constraints and flexible deployment the ACN is implemented as a multi-tier architecture. As such, it provides an extension of the client-server model. For the agent framework different tiers implemented as different <a href="../api/connections/base#connection-objects">`Connections`</a>:

<img src="../assets/acn-tiers.png" alt="DHT" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>The `p2p_libp2p_mailbox` connection is not available yet.
</p>
</div>

## Trust and security

An agent can choose which connection to use depending on the resource and trust requirements:

- `p2p_libp2p` connection: the agent maintains a peer of the ACN. The agent does not need to trust any other entity.
- `p2p_libp2p_client` connection: the agent maintains a client connection to a server which is operated by a peer of the ACN. The agent does need to trust the entity operating the peer.

The main protocol uses public cryptography to provide trust and security:
- DHT process starts with a public key pair signed by agent
- Lookup for agent addresses includes agent signature
- TLS handshake (with self-signed certificates)

<img src="../assets/acn-trust-security.png" alt="DHT" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">


<br />
