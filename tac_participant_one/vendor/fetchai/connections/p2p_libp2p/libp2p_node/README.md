
The `libp2p_node` is an integral part of the ACN.

## ACN - Agent Communication Network

The agent communication network (ACN) provides a system for agents to find each other and communicate, solely based on their wallet addresses. It addresses the message delivery problem.

For more details check out the [docs](https://github.com/fetchai/agents-aea/blob/main/docs/acn.md).

## Development

To run all tests run:

``` bash
go test -p 1 -timeout 0 -count 1 -v ./...
```

To lint:

``` bash
golines . -w
golangci-lint run
staticcheck ./...
```

For mocks generation:
check https://github.com/golang/mock

## Messaging patterns

Interaction protocol
___
ACN
___
TCP/UDP/...
___

### Messaging patterns inwards ACN:


Connection (`p2p_libp2p_client`) > Delegate Client > Relay Peer > Peer (Discouraged!)

Connection (`p2p_libp2p_client`)  > Delegate Client > Peer

Connection (`p2p_libp2p`) > Relay Peer > Peer

Connection (`p2p_libp2p`) > Peer


### Messaging patterns outwards ACN


Peer > Relay Peer > Delegate Client > Connection (`p2p_libp2p_client`) (Discouraged!)

Peer > Relay Peer > Connection (`p2p_libp2p`)

Peer > Delegate Client > Connection (`p2p_libp2p_client`)

Peer > Connection (`p2p_libp2p`)


In total 4*4 = 16 patterns (practically: 3*3 = 9 patterns)

## Guarantees

ACN should guarantee total ordering of messages for all agent pairs, independent of the type of connection and ACN messaging pattern used.

## Advanced feature (post `v1`):

Furthermore, there is the agent mobility. An agent can move between entry-points (Relay Peer/Peer/Delegate Client). The ACN must ensure that all messaging patterns maintain total ordering of messages for agent pairs during the move.

## ACN protocols

The ACN has the following protocols:

- register
- lookup
- unregister (dealt with by DHT defaults)
- DHT default protocols in libp2p
- message delivery protocol
