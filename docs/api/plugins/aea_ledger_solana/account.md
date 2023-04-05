<a id="plugins.aea-ledger-solana.aea_ledger_solana.account"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.account

Solana account implementation.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.account.AccountMeta"></a>

## AccountMeta Objects

```python
@dataclass
class AccountMeta()
```

Account metadata dataclass.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.account.AccountMeta.pubkey"></a>

#### pubkey

An account's public key.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.account.AccountMeta.is_signer"></a>

#### is`_`signer

True if an instruction requires a transaction signature matching `pubkey`

<a id="plugins.aea-ledger-solana.aea_ledger_solana.account.AccountMeta.is_writable"></a>

#### is`_`writable

True if the `pubkey` can be loaded as a read-write account.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.account.AccountMeta.from_solders"></a>

#### from`_`solders

```python
@classmethod
def from_solders(cls, meta: instruction.AccountMeta)
```

Convert from a `solders` AccountMeta.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.account.AccountMeta.to_solders"></a>

#### to`_`solders

```python
def to_solders() -> instruction.AccountMeta
```

Convert to a `solders` AccountMeta.

