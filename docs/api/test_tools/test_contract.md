<a id="aea.test_tools.test_contract"></a>

# aea.test`_`tools.test`_`contract

This module contains test case classes based on pytest for AEA contract testing.

<a id="aea.test_tools.test_contract.BaseContractTestCase"></a>

## BaseContractTestCase Objects

```python
class BaseContractTestCase(ABC)
```

A class to test a contract.

<a id="aea.test_tools.test_contract.BaseContractTestCase.contract"></a>

#### contract

```python
@property
def contract() -> Contract
```

Get the contract.

<a id="aea.test_tools.test_contract.BaseContractTestCase.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Set up the contract test case.

<a id="aea.test_tools.test_contract.BaseContractTestCase.finish_contract_deployment"></a>

#### finish`_`contract`_`deployment

```python
@classmethod
@abstractmethod
def finish_contract_deployment(cls) -> str
```

Finish deploying contract.

**Returns**:

contract address

<a id="aea.test_tools.test_contract.BaseContractTestCase.refill_from_faucet"></a>

#### refill`_`from`_`faucet

```python
@staticmethod
def refill_from_faucet(ledger_api: LedgerApi, faucet_api: FaucetApi,
                       address: str) -> None
```

Refill from faucet.

<a id="aea.test_tools.test_contract.BaseContractTestCase.sign_send_confirm_receipt_multisig_transaction"></a>

#### sign`_`send`_`confirm`_`receipt`_`multisig`_`transaction

```python
@staticmethod
def sign_send_confirm_receipt_multisig_transaction(
        tx: JSONLike,
        ledger_api: LedgerApi,
        cryptos: List[Crypto],
        sleep_time: float = 2.0) -> JSONLike
```

Sign, send and confirm settlement of a transaction with multiple signatures.

**Arguments**:

- `tx`: the transaction
- `ledger_api`: the ledger api
- `cryptos`: Cryptos to sign transaction with
- `sleep_time`: the time to sleep between transaction submission and receipt request

**Returns**:

The transaction receipt

<a id="aea.test_tools.test_contract.BaseContractTestCase.sign_send_confirm_receipt_transaction"></a>

#### sign`_`send`_`confirm`_`receipt`_`transaction

```python
@classmethod
def sign_send_confirm_receipt_transaction(cls,
                                          tx: JSONLike,
                                          ledger_api: LedgerApi,
                                          crypto: Crypto,
                                          sleep_time: float = 2.0) -> JSONLike
```

Sign, send and confirm settlement of a transaction with multiple signatures.

**Arguments**:

- `tx`: the transaction
- `ledger_api`: the ledger api
- `crypto`: Crypto to sign transaction with
- `sleep_time`: the time to sleep between transaction submission and receipt request

**Returns**:

The transaction receipt

