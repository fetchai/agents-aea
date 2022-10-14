<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai"></a>

# plugins.aea-ledger-fetchai.aea`_`ledger`_`fetchai.fetchai

Fetchai module wrapping the public and private key cryptography and ledger api.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIHelper"></a>

## FetchAIHelper Objects

```python
class FetchAIHelper(CosmosHelper)
```

Helper class usable as Mixin for FetchAIApi or as standalone class.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAICrypto"></a>

## FetchAICrypto Objects

```python
class FetchAICrypto(CosmosCrypto)
```

Class wrapping the Entity Generation from Fetch.AI ledger.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIApi"></a>

## FetchAIApi Objects

```python
class FetchAIApi(_CosmosApi,  FetchAIHelper)
```

Class to interact with the Fetch ledger APIs.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIApi.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the Fetch.ai ledger APIs.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIApi.contract_method_call"></a>

#### contract`_`method`_`call

```python
def contract_method_call(contract_instance: Any, method_name: str, **method_args: Any, ,) -> Optional[JSONLike]
```

Call a contract's method

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract call parameters

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIApi.build_transaction"></a>

#### build`_`transaction

```python
def build_transaction(contract_instance: Any, method_name: str, method_args: Optional[Dict], tx_args: Optional[Dict], raise_on_try: bool = False) -> Optional[JSONLike]
```

Prepare a transaction

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract parameters
- `tx_args`: the transaction parameters
- `raise_on_try`: whether the method will raise or log on error

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIApi.get_transaction_transfer_logs"></a>

#### get`_`transaction`_`transfer`_`logs

```python
def get_transaction_transfer_logs(contract_instance: Any, tx_hash: str, target_address: Optional[str] = None) -> Optional[JSONLike]
```

Get all transfer events derived from a transaction.

**Arguments**:

- `contract_instance`: the contract
- `tx_hash`: the transaction hash
- `target_address`: optional address to filter transfer events to just those that affect it

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.fetchai.FetchAIFaucetApi"></a>

## FetchAIFaucetApi Objects

```python
class FetchAIFaucetApi(CosmosFaucetApi)
```

Fetchai testnet faucet API.

