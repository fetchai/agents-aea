This page provides some tipps of how to upgrade between versions.

## v0.5.1 to 0.5.2

No public APIs have been changed.

## v0.5.0 to 0.5.1

No public APIs have been changed.

## v0.4.1 to 0.5.0

A number of breaking changes where introduced which make backwards compatibility of skills rare.

- Ledger apis <a href="../api/crypto/ledger_apis#ledger-apis-objects">`LedgerApis`</a> have been removed from the AEA constructor and skill context. `LedgerApis` are now exposed in the `LedgerConnection` (`fetchai/ledger`). To communicate with the `LedgerApis` use the `fetchai/ledger_api` protocol. This allows for more flexibility (anyone can add another `LedgerAPI` to the registry and execute it with the connection) and removes dependencies from the core framework.
- Skills can now depend on other skills. As a result, skills have a new required config field in `skill.yaml` files, by default empty: `skills: []`.

## v0.4.0 to v0.4.1

There are no upgrage requirements if you use the CLI based approach to AEA development.

Connections are now added via <a href="../api/registries/resources#resources-objects">`Resources`</a> to the AEA, not the AEA constructor directly. For programmatic usage remove the list of connections from the AEA constructor and instead add the connections to resources.

## v0.3.3 to v0.4.0

<ul>
<li> Message sending in the skills has been updated. In the past you had to construct messages, then serialize them and place them in an envelope:

``` python
cfp_msg = FipaMessage(...)
self.context.outbox.put_message(
    to=opponent_addr,
    sender=self.context.agent_address,
    protocol_id=FipaMessage.protocol_id,
    message=FipaSerializer().encode(cfp_msg),
)
# or
cfp_msg = FipaMessage(...)
envelope = Envelope(
    to=opponent_addr,
    sender=self.context.agent_address,
    protocol_id=FipaMessage.protocol_id,
    message=FipaSerializer().encode(cfp_msg),
)
self.context.outbox.put(envelope)
```

Now this has been simplified to:
``` python
cfp_msg = FipaMessage(...)
cfp_msg.counterparty = opponent_addr
self.context.outbox.put_message(message=cfp_msg)
```

You must update your skills as the old implementation is no longer supported.
</li>
<li> Connection constructors have been simplified. In the past you had to implement both the `__init__` as well as the `from_config` methods of a Connection. Now you only have to implement the `__init__` method which by default at load time now receives the following kwargs: `configuration: ConnectionConfig, identity: Identity, crypto_store: CryptoStore`. See for example in the scaffold connection:

``` python
class MyScaffoldConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PublicId.from_str("fetchai/scaffold:0.1.0")

    def __init__(
        self,
        configuration: ConnectionConfig,
        identity: Identity,
        crypto_store: CryptoStore,
    ):
        """
        Initialize a connection to an SDK or API.

        :param configuration: the connection configuration.
        :param crypto_store: object to access the connection crypto objects.
        :param identity: the identity object.
        """
        super().__init__(
            configuration=configuration, crypto_store=crypto_store, identity=identity
        )
```

As a result of this feature, you are now able to pass key-pairs to your connections via the `CryptoStore`.

You must update your connections as the old implementation is no longer supported.
</li>
</ul>
