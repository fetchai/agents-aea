
The agent communication network (ACN) provides a system for agents to find each other and communicate, solely based on their wallet addresses. It addresses the message delivery problem.

## Message delivery problem
Agents need to contact each others. Given the wallet address of a target agent, how can the originator agent deliver a message to it whilst guaranteeing certain properties?

The properties we would like to have are:

- Reliability: with guarantees on message reception
- Authentication: to prevent impersonation
- Confidentiality: to prevent exposing sensitive information within the message
- Availability: some guarantees about the liveness of the service (tampering detection)

The problem statement and the agents framework context impose a number of design constraints:

- Distributed environment: no assumption are placed about the location of the agent, they can be anywhere in the publicly reachable internet
- Decentralized environment: no trusted central authority
- Support for resource-constrained devices

The ACN solves the above problem whilst providing the above guarantees and satisfying the constraints.

## Peers

The ACN is maintained by peers. Peers are not to be equated with agents. They are processes (usually distributed and decentralized) that together maintain the service. To use the service, agents need to associate themselves with peers. Thanks to digital signatures, the association between a given peer and agent can be verified by any participant in the system.

## Distributed hash table

At its core, the ACN implements a distributed hash table (DHT). A DHT is similar to a regular hash table in that it stores key-value pairs. However, storage is distributed across the participating machines (peers) with an efficient lookup operation. This is enabled by:

- Consistent hashing: decide responsibility for assignment of the DHT key-value storage
- Structured overlays: organize the participating peers in a well defined topology for efficient routing

<img src="../assets/dht.jpg" alt="DHT" class="center" style="display: block; margin-left: auto; margin-right: auto;width:50%;">

For the ACN, we use the DHT to store and maintain association between an agent address and the (network) location of its peer.


## N-tier architecture

To satisfy different resource constraints and flexible deployment the ACN is implemented as a multi-tier architecture. As such, it provides an extension of the client-server model. The agent framework exploits this by implementing different tiers as different <a href="../api/connections/base#connection-objects">`Connections`</a>:

<img src="../assets/acn-tiers.jpg" alt="DHT" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>The <code>p2p_libp2p_mailbox</code> connection is not available yet.
</p>
</div>

## Trust and security

An agent can choose which connection to use depending on the resource and trust requirements:

- `p2p_libp2p` connection: the agent maintains a peer of the ACN. The agent has full control over the peer and does not need to trust any other entity.
- `p2p_libp2p_client` connection: the agent maintains a client connection to a server which is operated by a peer of the ACN. The agent does need to trust the entity operating the peer.

All communication protocols use public cryptography to ensure security (authentication, confidentiality, and availability) using TLS handshakes with pre-shared public keys.

<img src="../assets/acn-trust-security.jpg" alt="DHT" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">


<br />
