<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.helper

This module contains the helpers for the solana ledger.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper"></a>

## SolanaHelper Objects

```python
class SolanaHelper(Helper)
```

Helper class usable as Mixin for SolanaApi or as standalone class.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.BlockhashCache"></a>

#### BlockhashCache

defined in SolanaAPi.__init__

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.load_contract_interface"></a>

#### load`_`contract`_`interface

```python
@classmethod
def load_contract_interface(
        cls,
        idl_file_path: Optional[Path] = None,
        program_keypair: Optional[Crypto] = None,
        program_address: Optional[str] = None,
        rpc_api: Optional[str] = None,
        bytecode_path: Optional[Path] = None) -> Dict[str, Any]
```

Load contract interface.

**Arguments**:

- `idl_file_path`: the file path to the IDL
- `program_keypair`: the program keypair
- `program_address`: the program address
- `rpc_api`: the rpc api
- `bytecode_path`: the file path to the bytecode

**Returns**:

the interface

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.is_transaction_valid"></a>

#### is`_`transaction`_`valid

```python
@staticmethod
def is_transaction_valid(tx: JSONLike, seller: Address, client: Address,
                         tx_nonce: str, amount: int) -> bool
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.
# noqa: DAR202

**Returns**:

True if the random_message is equals to tx['input']

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.is_transaction_settled"></a>

#### is`_`transaction`_`settled

```python
@staticmethod
def is_transaction_settled(tx_receipt: JSONLike) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_receipt`: the receipt associated to the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.get_hash"></a>

#### get`_`hash

```python
@staticmethod
def get_hash(message: bytes) -> str
```

Get the hash of a message.

**Arguments**:

- `message`: the message to be hashed.

**Returns**:

the hash of the message as a hex string.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.recover_message"></a>

#### recover`_`message

```python
@classmethod
def recover_message(cls,
                    message: bytes,
                    signature: str,
                    is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**TOBEIMPLEMENTED**

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used
# noqa: DAR202

**Returns**:

the recovered addresses

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.recover_public_keys_from_message"></a>

#### recover`_`public`_`keys`_`from`_`message

```python
@classmethod
def recover_public_keys_from_message(
        cls,
        message: bytes,
        signature: str,
        is_deprecated_mode: bool = False) -> Tuple[str, ...]
```

Get the public key used to produce the `signature` of the `message`

**TOBEIMPLEMENTED**

**Arguments**:

- `message`: raw bytes used to produce signature
- `signature`: signature of the message
- `is_deprecated_mode`: if the deprecated signing was used
# noqa: DAR202

**Returns**:

the recovered public keys

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.generate_tx_nonce"></a>

#### generate`_`tx`_`nonce

```python
@staticmethod
def generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a unique hash to distinguish transactions with the same terms.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.add_nonce"></a>

#### add`_`nonce

```python
def add_nonce(tx: dict) -> JSONLike
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.to_transaction_format"></a>

#### to`_`transaction`_`format

```python
@staticmethod
def to_transaction_format(tx: dict) -> Any
```

Check whether a transaction is valid or not.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.to_dict_format"></a>

#### to`_`dict`_`format

```python
@staticmethod
def to_dict_format(tx) -> JSONLike
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.get_contract_address"></a>

#### get`_`contract`_`address

```python
@staticmethod
def get_contract_address(tx_receipt: JSONLike) -> Optional[str]
```

Retrieve the `contract_addresses` from a transaction receipt.

**Solana can have many contract addresses in one tx**

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the contract address, if present

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.get_address_from_public_key"></a>

#### get`_`address`_`from`_`public`_`key

```python
@classmethod
def get_address_from_public_key(cls, public_key: str) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a id="plugins.aea-ledger-solana.aea_ledger_solana.helper.SolanaHelper.is_valid_address"></a>

#### is`_`valid`_`address

```python
@classmethod
def is_valid_address(cls, address: str) -> bool
```

Check if the address is valid.

**Arguments**:

- `address`: the address to validate

**Returns**:

whether the address is valid

