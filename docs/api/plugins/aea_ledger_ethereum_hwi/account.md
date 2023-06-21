<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account"></a>

# plugins.aea-ledger-ethereum-hwi.aea`_`ledger`_`ethereum`_`hwi.account

Custom implementation of `eth_account.Account` for hardware wallets.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.chunk"></a>

#### chunk

```python
def chunk(seq: bytes, size: int) -> List[bytes]
```

Converts a byte sequence to a list of chunks

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccountData"></a>

## HWIAccountData Objects

```python
class HWIAccountData(NamedTuple)
```

Hardware wallet account data

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWISignedTransaction"></a>

## HWISignedTransaction Objects

```python
class HWISignedTransaction(NamedTuple)
```

Hardware wallet signed transaction

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.UnsignedDynamicTransaction"></a>

## UnsignedDynamicTransaction Objects

```python
class UnsignedDynamicTransaction(HashableRLP)
```

Unsigned dynamic transaction.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.UnsignedType1Transaction"></a>

## UnsignedType1Transaction Objects

```python
class UnsignedType1Transaction(HashableRLP)
```

Unsigned typ1 transaction

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.SignTransactionAPDU"></a>

## SignTransactionAPDU Objects

```python
class SignTransactionAPDU()
```

Sign transaction APDU codes

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.GetAccountAPDU"></a>

## GetAccountAPDU Objects

```python
class GetAccountAPDU()
```

Get account APDU codes

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIErrorCodes"></a>

## HWIErrorCodes Objects

```python
class HWIErrorCodes()
```

HWI com errors.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.reraise_from_hwi_com_error"></a>

#### reraise`_`from`_`hwi`_`com`_`error

```python
@contextmanager
def reraise_from_hwi_com_error() -> Generator
```

Reraise ledger communication exception as `HWIError`

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount"></a>

## HWIAccount Objects

```python
class HWIAccount()
```

Hardware wallet interface as ethereum account similar to `eth_account.Account` to represent `Crypto.entity`

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.__init__"></a>

#### `__`init`__`

```python
def __init__(default_device_index: int = 0,
             default_account_index: int = 0,
             default_key_index: int = 0) -> None
```

Initialize object.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.devices"></a>

#### devices

```python
@property
def devices() -> List[Any]
```

Returns the list of available devices.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.get_client"></a>

#### get`_`client

```python
def get_client(device_index: Optional[int] = None) -> LedgerClient
```

Get ledger client.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.get_account"></a>

#### get`_`account

```python
def get_account(key_index: Optional[int] = None,
                account_index: Optional[int] = None,
                device_index: Optional[int] = None) -> HWIAccountData
```

Get hardware wallet account.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.address"></a>

#### address

```python
@property
def address() -> ChecksumAddress
```

Address

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> ChecksumAddress
```

Public key

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.sign_message"></a>

#### sign`_`message

```python
def sign_message(signable_message: SignableMessage,
                 **kwargs: Any) -> SignedMessage
```

Sign a EIP191 message

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.encode_transaction"></a>

#### encode`_`transaction

```python
@staticmethod
def encode_transaction(transaction: TypedTransaction,
                       is_eip1559_tx: bool = False,
                       key_index: Optional[int] = None,
                       account_index: Optional[int] = None) -> bytes
```

Build and encode transaction

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.account.HWIAccount.sign_transaction"></a>

#### sign`_`transaction

```python
def sign_transaction(transaction_dict: JSONLike,
                     **kwargs: Any) -> SignedTransaction
```

Sign transaction.

