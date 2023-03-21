<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.solana

Solana module wrapping the public and private key cryptography and ledger api.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto"></a>

## SolanaCrypto Objects

```python
class SolanaCrypto(Crypto[Keypair])
```

Class wrapping the Account Generation from Solana ledger.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.__init__"></a>

#### `__`init`__`

```python
def __init__(private_key_path: Optional[str] = None,
             password: Optional[str] = None,
             extra_entropy: Union[str, bytes, int] = "") -> None
```

Instantiate an solana crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent
- `password`: the password to encrypt/decrypt the private key.
- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.private_key"></a>

#### private`_`key

```python
@property
def private_key() -> str
```

Return a private key.

64 random hex characters (i.e. 32 bytes) prefix.

**Returns**:

a private key string in hex format

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.address"></a>

#### address

```python
@property
def address() -> str
```

Return the address for the key pair.

**Returns**:

an address string in hex format

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.load_private_key_from_path"></a>

#### load`_`private`_`key`_`from`_`path

```python
@classmethod
def load_private_key_from_path(cls,
                               file_name: str,
                               password: Optional[str] = None) -> Keypair
```

Load a private key in base58 or bytes format from a file.

**Arguments**:

- `file_name`: the path to the hex file.
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the Entity.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.sign_message"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.sign_transaction"></a>

#### sign`_`transaction

```python
def sign_transaction(transaction: JSONLike,
                     signers: Optional[list] = None) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed
- `signers`: list of signers

**Returns**:

signed transaction

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.generate_private_key"></a>

#### generate`_`private`_`key

```python
@classmethod
def generate_private_key(cls,
                         extra_entropy: Union[str, bytes,
                                              int] = "") -> Keypair
```

Generate a key pair for Solana network.

**Arguments**:

- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

**Returns**:

keypair object

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.encrypt"></a>

#### encrypt

```python
def encrypt(password: str) -> str
```

Encrypt the private key and return in json.

**Arguments**:

- `password`: the password to decrypt.

**Returns**:

json string containing encrypted private key.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaCrypto.decrypt"></a>

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

the raw private key.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper"></a>

## SolanaHelper Objects

```python
class SolanaHelper(Helper)
```

Helper class usable as Mixin for SolanaApi or as standalone class.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.load_contract_interface"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.is_transaction_valid"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.is_transaction_settled"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.get_hash"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.recover_message"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.recover_public_keys_from_message"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.generate_tx_nonce"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.add_nonce"></a>

#### add`_`nonce

```python
def add_nonce(tx: dict) -> JSONLike
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.to_transaction_format"></a>

#### to`_`transaction`_`format

```python
@staticmethod
def to_transaction_format(tx: dict) -> Any
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.to_dict_format"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.get_contract_address"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.get_address_from_public_key"></a>

#### get`_`address`_`from`_`public`_`key

```python
@classmethod
def get_address_from_public_key(cls, public_key: PublicKey) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaHelper.is_valid_address"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi"></a>

## SolanaApi Objects

```python
class SolanaApi(LedgerApi, SolanaHelper)
```

Class to interact with the Solana Web3 APIs.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize the Solana ledger APIs.

**Arguments**:

- `kwargs`: keyword arguments

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.api"></a>

#### api

```python
@property
def api() -> Client
```

Get the underlying API object.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.update_with_gas_estimate"></a>

#### update`_`with`_`gas`_`estimate

```python
def update_with_gas_estimate(transaction: JSONLike) -> JSONLike
```

Attempts to update the transaction with a gas estimate

**NOT APPLICABLE**

**Arguments**:

- `transaction`: the transaction

**Returns**:

the updated transaction

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_balance"></a>

#### get`_`balance

```python
def get_balance(address: Address, raise_on_try: bool = False) -> Optional[int]
```

Get the balance of a given account.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_state"></a>

#### get`_`state

```python
def get_state(callable_name: str,
              *args: Any,
              raise_on_try: bool = False,
              **kwargs: Any) -> Optional[JSONLike]
```

Call a specified function on the underlying ledger API.

This usually takes the form of a web request to be waited synchronously.

**Arguments**:

- `callable_name`: the name of the API function to be called.
- `args`: the positional arguments for the API function.
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: the keyword arguments for the API function.

**Returns**:

the ledger API response.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_transfer_transaction"></a>

#### get`_`transfer`_`transaction

```python
def get_transfer_transaction(sender_address: Address,
                             destination_address: Address, amount: int,
                             tx_fee: int, tx_nonce: str,
                             **kwargs: Any) -> Optional[JSONLike]
```

Submit a transfer transaction to the ledger.

**Arguments**:

- `sender_address`: the sender address of the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred.
- `tx_fee`: the transaction fee.
- `tx_nonce`: verifies the authenticity of the tx
- `kwargs`: the keyword arguments.

**Returns**:

the transfer transaction

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.send_signed_transaction"></a>

#### send`_`signed`_`transaction

```python
def send_signed_transaction(tx_signed: JSONLike,
                            raise_on_try: bool = False) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

tx_digest, if present

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.send_signed_transactions"></a>

#### send`_`signed`_`transactions

```python
def send_signed_transactions(signed_transactions: List[JSONLike],
                             raise_on_try: bool = False,
                             **kwargs: Any) -> Optional[List[str]]
```

Atomically send multiple of transactions.

**Arguments**:

- `signed_transactions`: the signed transactions to bundle together and send.
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: the keyword arguments.

**Returns**:

the transaction digest if the transactions went through, None otherwise.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_transaction_receipt"></a>

#### get`_`transaction`_`receipt

```python
def get_transaction_receipt(tx_digest: str,
                            raise_on_try: bool = False) -> Optional[JSONLike]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the tx receipt, if present

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_transaction"></a>

#### get`_`transaction

```python
def get_transaction(tx_digest: str,
                    raise_on_try: bool = False) -> Optional[JSONLike]
```

Get the transaction for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the tx, if present

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.create_default_account"></a>

#### create`_`default`_`account

```python
@staticmethod
def create_default_account(from_address: str,
                           new_account_address: str,
                           lamports: int,
                           space: int,
                           program_id: Optional[str] = SYS_PROGRAM_ID)
```

Build a create account transaction.

**Arguments**:

- `from_address`: the sender public key
- `new_account_address`: the new account public key
- `lamports`: the amount of lamports to send
- `space`: the space to allocate
- `program_id`: the program id

**Returns**:

the tx, if present

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.create_pda"></a>

#### create`_`pda

```python
@staticmethod
def create_pda(from_address: str, new_account_address: str, base_address: str,
               seed: str, lamports: int, space: int, program_id: str)
```

Build a create pda transaction.

**Arguments**:

- `from_address`: the sender public key
- `new_account_address`: the new account public key
- `base_address`: base address
- `seed`: seed
- `lamports`: the amount of lamports to send
- `space`: the space to allocate
- `program_id`: the program id

**Returns**:

the tx, if present

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_contract_instance"></a>

#### get`_`contract`_`instance

```python
def get_contract_instance(contract_interface: Dict[str, str],
                          contract_address: Optional[str] = None) -> Any
```

Get the instance of a contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `contract_address`: the contract address.

**Returns**:

the contract instance

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_deploy_transaction"></a>

#### get`_`deploy`_`transaction

```python
def get_deploy_transaction(contract_interface: Dict[str, str],
                           deployer_address: Address,
                           raise_on_try: bool = False,
                           **kwargs: Any) -> Optional[JSONLike]
```

Get the transaction to deploy the smart contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `deployer_address`: The address that will deploy the contract.
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: the keyword arguments.

**Returns**:

`tx`: the transaction dictionary.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.contract_method_call"></a>

#### contract`_`method`_`call

```python
def contract_method_call(contract_instance: Any, method_name: str,
                         **method_args: Any) -> Optional[JSONLike]
```

Call a contract's method

**TOBEIMPLEMENTED**

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract call parameters
# noqa: DAR202

**Returns**:

the call result

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.build_transaction"></a>

#### build`_`transaction

```python
def build_transaction(contract_instance: Any,
                      method_name: str,
                      method_args: Optional[Dict[Any, Any]],
                      tx_args: Optional[Dict[Any, Any]],
                      raise_on_try: bool = False) -> Optional[JSONLike]
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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaApi.get_transaction_transfer_logs"></a>

#### get`_`transaction`_`transfer`_`logs

```python
def get_transaction_transfer_logs(
        contract_instance: Any,
        tx_hash: str,
        target_address: Optional[str] = None) -> Optional[JSONLike]
```

Get all transfer events derived from a transaction.

**Arguments**:

- `contract_instance`: contract instance
- `tx_hash`: the transaction hash
- `target_address`: optional address to filter tranfer events to just those that affect it

**Returns**:

the transfer logs

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaFaucetApi"></a>

## SolanaFaucetApi Objects

```python
class SolanaFaucetApi(FaucetApi)
```

Solana testnet faucet API.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.solana.SolanaFaucetApi.get_wealth"></a>

#### get`_`wealth

```python
def get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

