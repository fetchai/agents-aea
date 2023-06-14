<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots"></a>

# plugins.aea-ledger-ethereum-flashbots.aea`_`ledger`_`ethereum`_`flashbots.ethereum`_`flashbots

Python package extending the default open-aea ethereum ledger plugin to add support for flashbots.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.multiple_flashbots_builders"></a>

#### multiple`_`flashbots`_`builders

```python
def multiple_flashbots_builders(
        signature_account: LocalAccount,
        builders: List[Tuple[str, str]],
        rpc_endpoint: str = DEFAULT_ADDRESS) -> Dict[str, Web3]
```

Setup multiple flashbots providers.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi"></a>

## EthereumFlashbotApi Objects

```python
class EthereumFlashbotApi(EthereumApi)
```

Class to interact with the Ethereum Web3 APIs.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize the Ethereum API.

**Arguments**:

- `kwargs`: the keyword arguments.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.flashbots"></a>

#### flashbots

```python
@property
def flashbots() -> Flashbots
```

Get the flashbots Web3 module.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.send_to_all_builders"></a>

#### send`_`to`_`all`_`builders

```python
def send_to_all_builders(
        bundle: List[FlashbotsBundleRawTx], target_block: int,
        opts: Dict[str, Any]) -> Dict[str, FlashbotsBundleResponse]
```

Send the transaction to multiple builders.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.bundle_transactions"></a>

#### bundle`_`transactions

```python
@staticmethod
def bundle_transactions(
        signed_transactions: List[JSONLike]) -> List[FlashbotsBundleRawTx]
```

Bundle transactions.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.simulate"></a>

#### simulate

```python
def simulate(bundle: List[Union[FlashbotsBundleTx, FlashbotsBundleRawTx]],
             target_block: Optional[int]) -> bool
```

Simulate a bundle.

1. Simulate the bundle in a try catch block.
2. Return True if simulation went through, or False if something went wrong.

**Arguments**:

- `bundle`: the bundle to simulate.
- `target_block`: the target block for the transaction, the current block if not provided.

**Returns**:

True if the simulation went through, False otherwise.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.send_bundle"></a>

#### send`_`bundle

```python
def send_bundle(bundle: List[Union[FlashbotsBundleTx, FlashbotsBundleRawTx]],
                target_blocks: List[int],
                raise_on_failed_simulation: bool = False,
                use_all_builders: bool = False) -> Optional[List[str]]
```

Send a bundle.

1. Simulate the bundle.
2. Send the bundle in a try catch block.
3. Wait for the response. If successful, go to step 4.
 If current block number is less than the maximum target block number, go to step 1.
4. Return the transaction digests if the transactions went through, or None if something went wrong.

**Arguments**:

- `bundle`: the signed transactions to bundle together and send.
- `target_blocks`: the target blocks for the transactions.
- `raise_on_failed_simulation`: whether to raise an exception if the simulation fails.
- `use_all_builders`: whether to send the bundle to all builders.

**Returns**:

the transaction digest if the transaction went through, None otherwise.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotApi.send_signed_transactions"></a>

#### send`_`signed`_`transactions

```python
def send_signed_transactions(signed_transactions: List[JSONLike],
                             raise_on_try: bool = False,
                             **kwargs: Any) -> Optional[List[str]]
```

Simulate and send a bundle of transactions.

**Arguments**:

- `signed_transactions`: the raw signed transactions to bundle together and send.
- `raise_on_try`: whether to raise an exception if the transaction is not successful.
- `kwargs`: the keyword arguments.

**Returns**:

the transaction digest if the transactions went through, None otherwise.

<a id="plugins.aea-ledger-ethereum-flashbots.aea_ledger_ethereum_flashbots.ethereum_flashbots.EthereumFlashbotCrypto"></a>

## EthereumFlashbotCrypto Objects

```python
class EthereumFlashbotCrypto(EthereumCrypto)
```

Class wrapping the Account Generation from Ethereum ledger.

