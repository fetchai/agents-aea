<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum"></a>
# plugins.aea-ledger-ethereum.aea`_`ledger`_`ethereum.ethereum

Ethereum module wrapping the public and private key cryptography and ledger api.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.get_gas_price_strategy"></a>
#### get`_`gas`_`price`_`strategy

```python
get_gas_price_strategy(gas_price_strategy: Optional[str] = None, api_key: Optional[str] = None) -> Callable[[Web3, TxParams], Wei]
```

Get the gas price strategy.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.SignedTransactionTranslator"></a>
## SignedTransactionTranslator Objects

```python
class SignedTransactionTranslator()
```

Translator for SignedTransaction.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.SignedTransactionTranslator.to_dict"></a>
#### to`_`dict

```python
 | @staticmethod
 | to_dict(signed_transaction: SignedTransaction) -> Dict[str, Union[str, int]]
```

Write SignedTransaction to dict.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.SignedTransactionTranslator.from_dict"></a>
#### from`_`dict

```python
 | @staticmethod
 | from_dict(signed_transaction_dict: JSONLike) -> SignedTransaction
```

Get SignedTransaction from dict.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.AttributeDictTranslator"></a>
## AttributeDictTranslator Objects

```python
class AttributeDictTranslator()
```

Translator for AttributeDict.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.AttributeDictTranslator.to_dict"></a>
#### to`_`dict

```python
 | @classmethod
 | to_dict(cls, attr_dict: Union[AttributeDict, TxReceipt, TxData]) -> JSONLike
```

Simplify to dict.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.AttributeDictTranslator.from_dict"></a>
#### from`_`dict

```python
 | @classmethod
 | from_dict(cls, di: JSONLike) -> AttributeDict
```

Get back attribute dict.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto"></a>
## EthereumCrypto Objects

```python
class EthereumCrypto(Crypto[Account])
```

Class wrapping the Account Generation from Ethereum ledger.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_path: Optional[str] = None, password: Optional[str] = None) -> None
```

Instantiate an ethereum crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent
- `password`: the password to encrypt/decrypt the private key.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.private_key"></a>
#### private`_`key

```python
 | @property
 | private_key() -> str
```

Return a private key.

**Returns**:

a private key string

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.address"></a>
#### address

```python
 | @property
 | address() -> str
```

Return the address for the key pair.

**Returns**:

a display_address str

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.load_private_key_from_path"></a>
#### load`_`private`_`key`_`from`_`path

```python
 | @classmethod
 | load_private_key_from_path(cls, file_name: str, password: Optional[str] = None) -> Account
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the Entity.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.sign_message"></a>
#### sign`_`message

```python
 | sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message to be signed
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.sign_transaction"></a>
#### sign`_`transaction

```python
 | sign_transaction(transaction: JSONLike) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.generate_private_key"></a>
#### generate`_`private`_`key

```python
 | @classmethod
 | generate_private_key(cls) -> Account
```

Generate a key pair for ethereum network.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.encrypt"></a>
#### encrypt

```python
 | encrypt(password: str) -> str
```

Encrypt the private key and return in json.

**Arguments**:

- `password`: the password to decrypt.

**Returns**:

json string containing encrypted private key.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.decrypt"></a>
#### decrypt

```python
 | @classmethod
 | decrypt(cls, keyfile_json: str, password: str) -> str
```

Decrypt the private key and return in raw form.

**Arguments**:

- `keyfile_json`: json str containing encrypted private key.
- `password`: the password to decrypt.

**Returns**:

the raw private key.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper"></a>
## EthereumHelper Objects

```python
class EthereumHelper(Helper)
```

Helper class usable as Mixin for EthereumApi or as standalone class.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | @staticmethod
 | is_transaction_settled(tx_receipt: JSONLike) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_receipt`: the receipt associated to the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.get_contract_address"></a>
#### get`_`contract`_`address

```python
 | @staticmethod
 | get_contract_address(tx_receipt: JSONLike) -> Optional[str]
```

Retrieve the `contract_address` from a transaction receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the contract address, if present

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.is_transaction_valid"></a>
#### is`_`transaction`_`valid

```python
 | @staticmethod
 | is_transaction_valid(tx: dict, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | @staticmethod
 | generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a unique hash to distinguish transactions with the same terms.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.get_address_from_public_key"></a>
#### get`_`address`_`from`_`public`_`key

```python
 | @classmethod
 | get_address_from_public_key(cls, public_key: str) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.recover_message"></a>
#### recover`_`message

```python
 | @classmethod
 | recover_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.recover_public_keys_from_message"></a>
#### recover`_`public`_`keys`_`from`_`message

```python
 | @classmethod
 | recover_public_keys_from_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[str, ...]
```

Get the public key used to produce the `signature` of the `message`

**Arguments**:

- `message`: raw bytes used to produce signature
- `signature`: signature of the message
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered public keys

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.get_hash"></a>
#### get`_`hash

```python
 | @staticmethod
 | get_hash(message: bytes) -> str
```

Get the hash of a message.

**Arguments**:

- `message`: the message to be hashed.

**Returns**:

the hash of the message.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.load_contract_interface"></a>
#### load`_`contract`_`interface

```python
 | @classmethod
 | load_contract_interface(cls, file_path: Path) -> Dict[str, str]
```

Load contract interface.

**Arguments**:

- `file_path`: the file path to the interface

**Returns**:

the interface

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi"></a>
## EthereumApi Objects

```python
class EthereumApi(LedgerApi,  EthereumHelper)
```

Class to interact with the Ethereum Web3 APIs.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs: Any)
```

Initialize the Ethereum ledger APIs.

**Arguments**:

- `kwargs`: keyword arguments

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.api"></a>
#### api

```python
 | @property
 | api() -> Web3
```

Get the underlying API object.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_balance"></a>
#### get`_`balance

```python
 | get_balance(address: Address) -> Optional[int]
```

Get the balance of a given account.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_state"></a>
#### get`_`state

```python
 | get_state(callable_name: str, *args: Any, **kwargs: Any) -> Optional[JSONLike]
```

Call a specified function on the ledger API.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transfer_transaction"></a>
#### get`_`transfer`_`transaction

```python
 | get_transfer_transaction(sender_address: Address, destination_address: Address, amount: int, tx_fee: int, tx_nonce: str, chain_id: Optional[int] = None, gas_price: Optional[str] = None, gas_price_strategy: Optional[str] = None, **kwargs: Any, ,) -> Optional[JSONLike]
```

Submit a transfer transaction to the ledger.

**Arguments**:

- `sender_address`: the sender address of the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred (in Wei).
- `tx_fee`: the transaction fee (gas) to be used (in Wei).
- `tx_nonce`: verifies the authenticity of the tx.
- `chain_id`: the Chain ID of the Ethereum transaction.
- `gas_price`: the gas price (in Wei)
- `gas_price_strategy`: the gas price strategy to be used.
- `kwargs`: keyword arguments

**Returns**:

the transfer transaction

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.update_with_gas_estimate"></a>
#### update`_`with`_`gas`_`estimate

```python
 | update_with_gas_estimate(transaction: JSONLike) -> JSONLike
```

Attempts to update the transaction with a gas estimate

**Arguments**:

- `transaction`: the transaction

**Returns**:

the updated transaction

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(tx_signed: JSONLike) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction

**Returns**:

tx_digest, if present

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transaction_receipt"></a>
#### get`_`transaction`_`receipt

```python
 | get_transaction_receipt(tx_digest: str) -> Optional[JSONLike]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx receipt, if present

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transaction"></a>
#### get`_`transaction

```python
 | get_transaction(tx_digest: str) -> Optional[JSONLike]
```

Get the transaction for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx, if present

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_contract_instance"></a>
#### get`_`contract`_`instance

```python
 | get_contract_instance(contract_interface: Dict[str, str], contract_address: Optional[str] = None) -> Any
```

Get the instance of a contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `contract_address`: the contract address.

**Returns**:

the contract instance

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_deploy_transaction"></a>
#### get`_`deploy`_`transaction

```python
 | get_deploy_transaction(contract_interface: Dict[str, str], deployer_address: Address, value: int = 0, gas: int = 0, gas_price: Optional[str] = None, gas_price_strategy: Optional[str] = None, **kwargs: Any, ,) -> Optional[JSONLike]
```

Get the transaction to deploy the smart contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `deployer_address`: The address that will deploy the contract.
- `value`: value to send to contract (in Wei)
- `gas`: the gas to be used (in Wei)
- `gas_price`: the gas price (in Wei)
- `gas_price_strategy`: the gas price strategy to be used.
- `kwargs`: keyword arguments

**Returns**:

the transaction dictionary.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.is_valid_address"></a>
#### is`_`valid`_`address

```python
 | @classmethod
 | is_valid_address(cls, address: Address) -> bool
```

Check if the address is valid.

**Arguments**:

- `address`: the address to validate

**Returns**:

whether the address is valid

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumFaucetApi"></a>
## EthereumFaucetApi Objects

```python
class EthereumFaucetApi(FaucetApi)
```

Ethereum testnet faucet API.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumFaucetApi.get_wealth"></a>
#### get`_`wealth

```python
 | get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper"></a>
## LruLockWrapper Objects

```python
class LruLockWrapper()
```

Wrapper for LRU with threading.Lock.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__init__"></a>
#### `__`init`__`

```python
 | __init__(lru: LRU) -> None
```

Init wrapper.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__getitem__"></a>
#### `__`getitem`__`

```python
 | __getitem__(*args: Any, **kwargs: Any) -> Any
```

Get item

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__setitem__"></a>
#### `__`setitem`__`

```python
 | __setitem__(*args: Any, **kwargs: Any) -> Any
```

Set item.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__contains__"></a>
#### `__`contains`__`

```python
 | __contains__(*args: Any, **kwargs: Any) -> Any
```

Contain item.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__delitem__"></a>
#### `__`delitem`__`

```python
 | __delitem__(*args: Any, **kwargs: Any) -> Any
```

Del item.

<a name="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.set_wrapper_for_web3py_session_cache"></a>
#### set`_`wrapper`_`for`_`web3py`_`session`_`cache

```python
set_wrapper_for_web3py_session_cache() -> None
```

Wrap web3py session cache with threading.Lock.

