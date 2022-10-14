<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum"></a>

# plugins.aea-ledger-ethereum.aea`_`ledger`_`ethereum.ethereum

Ethereum module wrapping the public and private key cryptography and ledger api.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.wei_to_gwei"></a>

#### wei`_`to`_`gwei

```python
def wei_to_gwei(number: Type[int]) -> Union[int, decimal.Decimal]
```

Covert WEI to GWEI

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.round_to_whole_gwei"></a>

#### round`_`to`_`whole`_`gwei

```python
def round_to_whole_gwei(number: Type[int]) -> Wei
```

Round WEI to equivalent GWEI

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.get_base_fee_multiplier"></a>

#### get`_`base`_`fee`_`multiplier

```python
def get_base_fee_multiplier(base_fee_gwei: int) -> float
```

Returns multiplier value.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.estimate_priority_fee"></a>

#### estimate`_`priority`_`fee

```python
def estimate_priority_fee(web3_object: Web3, base_fee_gwei: int, block_number: int, priority_fee_estimation_trigger: int, default_priority_fee: int, fee_history_blocks: int, fee_history_percentile: int, priority_fee_increase_boundary: int) -> Optional[int]
```

Estimate priority fee from base fee.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.get_gas_price_strategy_eip1559"></a>

#### get`_`gas`_`price`_`strategy`_`eip1559

```python
def get_gas_price_strategy_eip1559(max_gas_fast: int, fee_history_blocks: int, fee_history_percentile: int, priority_fee_estimation_trigger: int, default_priority_fee: int, fallback_estimate: Dict[str, Optional[int]], priority_fee_increase_boundary: int) -> Callable[[Web3, TxParams], Dict[str, Wei]]
```

Get the gas price strategy.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.get_gas_price_strategy_eip1559_polygon"></a>

#### get`_`gas`_`price`_`strategy`_`eip1559`_`polygon

```python
def get_gas_price_strategy_eip1559_polygon(gas_endpoint: str, fallback_estimate: Dict[str, Optional[int]], speed: Optional[str] = SPEED_FAST) -> Callable[[Any, Any], Dict[str, Wei]]
```

Get the gas price strategy.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.rpc_gas_price_strategy_wrapper"></a>

#### rpc`_`gas`_`price`_`strategy`_`wrapper

```python
def rpc_gas_price_strategy_wrapper(web3: Web3, transaction_params: TxParams) -> Dict[str, Wei]
```

RPC gas price strategy wrapper.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.get_gas_price_strategy"></a>

#### get`_`gas`_`price`_`strategy

```python
def get_gas_price_strategy(gas_price_strategy: Optional[str] = None, gas_price_api_key: Optional[str] = None) -> Callable[[Web3, TxParams], Dict[str, Wei]]
```

Get the gas price strategy.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.SignedTransactionTranslator"></a>

## SignedTransactionTranslator Objects

```python
class SignedTransactionTranslator()
```

Translator for SignedTransaction.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.SignedTransactionTranslator.to_dict"></a>

#### to`_`dict

```python
@staticmethod
def to_dict(signed_transaction: SignedTransaction) -> Dict[str, Union[str, int]]
```

Write SignedTransaction to dict.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.SignedTransactionTranslator.from_dict"></a>

#### from`_`dict

```python
@staticmethod
def from_dict(signed_transaction_dict: JSONLike) -> SignedTransaction
```

Get SignedTransaction from dict.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.AttributeDictTranslator"></a>

## AttributeDictTranslator Objects

```python
class AttributeDictTranslator()
```

Translator for AttributeDict.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.AttributeDictTranslator.to_dict"></a>

#### to`_`dict

```python
@classmethod
def to_dict(cls, attr_dict: Union[AttributeDict, TxReceipt, TxData]) -> JSONLike
```

Simplify to dict.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.AttributeDictTranslator.from_dict"></a>

#### from`_`dict

```python
@classmethod
def from_dict(cls, di: JSONLike) -> AttributeDict
```

Get back attribute dict.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto"></a>

## EthereumCrypto Objects

```python
class EthereumCrypto(Crypto[LocalAccount])
```

Class wrapping the Account Generation from Ethereum ledger.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.__init__"></a>

#### `__`init`__`

```python
def __init__(private_key_path: Optional[str] = None, password: Optional[str] = None, extra_entropy: Union[str, bytes, int] = "") -> None
```

Instantiate an ethereum crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent
- `password`: the password to encrypt/decrypt the private key.
- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.private_key"></a>

#### private`_`key

```python
@property
def private_key() -> str
```

Return a private key.

64 random hex characters (i.e. 32 bytes) + "0x" prefix.

**Returns**:

a private key string in hex format

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Return a public key in hex format.

128 hex characters (i.e. 64 bytes) + "0x" prefix.

**Returns**:

a public key string in hex format

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.address"></a>

#### address

```python
@property
def address() -> str
```

Return the address for the key pair.

40 hex characters (i.e. 20 bytes) + "0x" prefix.

**Returns**:

an address string in hex format

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.load_private_key_from_path"></a>

#### load`_`private`_`key`_`from`_`path

```python
@classmethod
def load_private_key_from_path(cls, file_name: str, password: Optional[str] = None) -> LocalAccount
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the Entity.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.sign_message"></a>

#### sign`_`message

```python
def sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message to be signed
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.sign_transaction"></a>

#### sign`_`transaction

```python
def sign_transaction(transaction: JSONLike) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.generate_private_key"></a>

#### generate`_`private`_`key

```python
@classmethod
def generate_private_key(cls, extra_entropy: Union[str, bytes, int] = "") -> LocalAccount
```

Generate a key pair for ethereum network.

**Arguments**:

- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

**Returns**:

account object

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.encrypt"></a>

#### encrypt

```python
def encrypt(password: str) -> str
```

Encrypt the private key and return in json.

**Arguments**:

- `password`: the password to decrypt.

**Returns**:

json string containing encrypted private key.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumCrypto.decrypt"></a>

#### decrypt

```python
@classmethod
def decrypt(cls, keyfile_json: str, password: str) -> str
```

Decrypt the private key and return in raw form.

**Arguments**:

- `keyfile_json`: json str containing encrypted private key.
- `password`: the password to decrypt.

**Returns**:

the raw private key (without leading "0x").

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper"></a>

## EthereumHelper Objects

```python
class EthereumHelper(Helper)
```

Helper class usable as Mixin for EthereumApi or as standalone class.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.is_transaction_settled"></a>

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

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.get_contract_address"></a>

#### get`_`contract`_`address

```python
@staticmethod
def get_contract_address(tx_receipt: JSONLike) -> Optional[str]
```

Retrieve the `contract_address` from a transaction receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the contract address, if present

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.is_transaction_valid"></a>

#### is`_`transaction`_`valid

```python
@staticmethod
def is_transaction_valid(tx: dict, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
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

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.generate_tx_nonce"></a>

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

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.get_address_from_public_key"></a>

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

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.recover_message"></a>

#### recover`_`message

```python
@classmethod
def recover_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.recover_public_keys_from_message"></a>

#### recover`_`public`_`keys`_`from`_`message

```python
@classmethod
def recover_public_keys_from_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[str, ...]
```

Get the public key used to produce the `signature` of the `message`

**Arguments**:

- `message`: raw bytes used to produce signature
- `signature`: signature of the message
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered public keys

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.get_hash"></a>

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

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumHelper.load_contract_interface"></a>

#### load`_`contract`_`interface

```python
@classmethod
def load_contract_interface(cls, file_path: Path) -> Dict[str, str]
```

Load contract interface.

**Arguments**:

- `file_path`: the file path to the interface

**Returns**:

the interface

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi"></a>

## EthereumApi Objects

```python
class EthereumApi(LedgerApi,  EthereumHelper)
```

Class to interact with the Ethereum Web3 APIs.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize the Ethereum ledger APIs.

**Arguments**:

- `kwargs`: keyword arguments

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.api"></a>

#### api

```python
@property
def api() -> Web3
```

Get the underlying API object.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_balance"></a>

#### get`_`balance

```python
def get_balance(address: Address, raise_on_try: bool = False) -> Optional[int]
```

Get the balance of a given account.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_state"></a>

#### get`_`state

```python
def get_state(callable_name: str, *args: Any, *, raise_on_try: bool = False, **kwargs: Any) -> Optional[JSONLike]
```

Call a specified function on the ledger API.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transfer_transaction"></a>

#### get`_`transfer`_`transaction

```python
def get_transfer_transaction(sender_address: Address, destination_address: Address, amount: int, tx_fee: int, tx_nonce: str, chain_id: Optional[int] = None, max_fee_per_gas: Optional[int] = None, max_priority_fee_per_gas: Optional[str] = None, gas_price: Optional[str] = None, gas_price_strategy: Optional[str] = None, gas_price_strategy_extra_config: Optional[Dict] = None, raise_on_try: bool = False, **kwargs: Any, ,) -> Optional[JSONLike]
```

Submit a transfer transaction to the ledger.

**Arguments**:

- `sender_address`: the sender address of the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred (in Wei).
- `tx_fee`: the transaction fee (gas) to be used (in Wei).
- `tx_nonce`: verifies the authenticity of the tx.
- `chain_id`: the Chain ID of the Ethereum transaction.
- `max_fee_per_gas`: maximum amount you’re willing to pay, inclusive of `baseFeePerGas` and `maxPriorityFeePerGas`. The difference between `maxFeePerGas` and `baseFeePerGas + maxPriorityFeePerGas` is refunded  (in Wei).
- `max_priority_fee_per_gas`: the part of the fee that goes to the miner (in Wei).
- `gas_price`: the gas price (in Wei)
- `gas_price_strategy`: the gas price strategy to be used.
- `gas_price_strategy_extra_config`: extra config for gas price strategy.
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: keyword arguments

**Returns**:

the transfer transaction

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.try_get_gas_pricing"></a>

#### try`_`get`_`gas`_`pricing

```python
@try_decorator("Unable to retrieve gas price: {}", logger_method="warning")
def try_get_gas_pricing(gas_price_strategy: Optional[str] = None, extra_config: Optional[Dict] = None, old_price: Optional[Dict[str, Wei]] = None, **_kwargs: Any, ,) -> Optional[Dict[str, Wei]]
```

Try get the gas price based on the provided strategy.

**Arguments**:

    Can be either `eip1559` or `gas_station`.
    `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
- `gas_price_strategy`: the gas price strategy to use, e.g., the EIP-1559 strategy.
- `extra_config`: gas price strategy getter parameters.
- `old_price`: the old gas price params in case that we are trying to resubmit a transaction.
- `_kwargs`: the keyword arguments. Possible kwargs are:

**Returns**:

a dictionary with the gas data.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.update_with_gas_estimate"></a>

#### update`_`with`_`gas`_`estimate

```python
def update_with_gas_estimate(transaction: JSONLike) -> JSONLike
```

Attempts to update the transaction with a gas estimate

**Arguments**:

- `transaction`: the transaction

**Returns**:

the updated transaction

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.send_signed_transaction"></a>

#### send`_`signed`_`transaction

```python
def send_signed_transaction(tx_signed: JSONLike, raise_on_try: bool = False) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

tx_digest, if present

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transaction_receipt"></a>

#### get`_`transaction`_`receipt

```python
def get_transaction_receipt(tx_digest: str, raise_on_try: bool = False) -> Optional[JSONLike]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the tx receipt, if present

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transaction"></a>

#### get`_`transaction

```python
def get_transaction(tx_digest: str, raise_on_try: bool = False) -> Optional[JSONLike]
```

Get the transaction for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the tx, if present

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_contract_instance"></a>

#### get`_`contract`_`instance

```python
def get_contract_instance(contract_interface: Dict[str, str], contract_address: Optional[str] = None) -> Any
```

Get the instance of a contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `contract_address`: the contract address.

**Returns**:

the contract instance

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_deploy_transaction"></a>

#### get`_`deploy`_`transaction

```python
def get_deploy_transaction(contract_interface: Dict[str, str], deployer_address: Address, raise_on_try: bool = False, **kwargs: Any, ,) -> Optional[JSONLike]
```

Get the transaction to deploy the smart contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `deployer_address`: The address that will deploy the contract.
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: keyword arguments

**Returns**:

the transaction dictionary.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.is_valid_address"></a>

#### is`_`valid`_`address

```python
@classmethod
def is_valid_address(cls, address: Address) -> bool
```

Check if the address is valid.

**Arguments**:

- `address`: the address to validate

**Returns**:

whether the address is valid

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.contract_method_call"></a>

#### contract`_`method`_`call

```python
@classmethod
def contract_method_call(cls, contract_instance: Any, method_name: str, **method_args: Any, ,) -> Optional[JSONLike]
```

Call a contract's method

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract call parameters

**Returns**:

the call result

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.build_transaction"></a>

#### build`_`transaction

```python
def build_transaction(contract_instance: Any, method_name: str, method_args: Optional[Dict[Any, Any]], tx_args: Optional[Dict[Any, Any]], raise_on_try: bool = False) -> Optional[JSONLike]
```

Prepare a transaction

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract parameters
- `tx_args`: the transaction parameters
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the transaction

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumApi.get_transaction_transfer_logs"></a>

#### get`_`transaction`_`transfer`_`logs

```python
def get_transaction_transfer_logs(contract_instance: Any, tx_hash: str, target_address: Optional[str] = None) -> Optional[JSONLike]
```

Get all transfer events derived from a transaction.

**Arguments**:

- `contract_instance`: the contract
- `tx_hash`: the transaction hash
- `target_address`: optional address to filter tranfer events to just those that affect it

**Returns**:

the transfer logs

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumFaucetApi"></a>

## EthereumFaucetApi Objects

```python
class EthereumFaucetApi(FaucetApi)
```

Ethereum testnet faucet API.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.EthereumFaucetApi.get_wealth"></a>

#### get`_`wealth

```python
def get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper"></a>

## LruLockWrapper Objects

```python
class LruLockWrapper()
```

Wrapper for LRU with threading.Lock.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__init__"></a>

#### `__`init`__`

```python
def __init__(lru: LRU) -> None
```

Init wrapper.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__getitem__"></a>

#### `__`getitem`__`

```python
def __getitem__(*args: Any, **kwargs: Any) -> Any
```

Get item

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__setitem__"></a>

#### `__`setitem`__`

```python
def __setitem__(*args: Any, **kwargs: Any) -> Any
```

Set item.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__contains__"></a>

#### `__`contains`__`

```python
def __contains__(*args: Any, **kwargs: Any) -> Any
```

Contain item.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.LruLockWrapper.__delitem__"></a>

#### `__`delitem`__`

```python
def __delitem__(*args: Any, **kwargs: Any) -> Any
```

Del item.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.ethereum.set_wrapper_for_web3py_session_cache"></a>

#### set`_`wrapper`_`for`_`web3py`_`session`_`cache

```python
def set_wrapper_for_web3py_session_cache() -> None
```

Wrap web3py session cache with threading.Lock.

