<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.fixture_helpers"></a>

# plugins.aea-ledger-ethereum.aea`_`ledger`_`ethereum.test`_`tools.fixture`_`helpers

Fixture helpers

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.fixture_helpers.ganache"></a>

#### ganache

```python
@pytest.fixture(scope="class")
def ganache(ganache_addr=DEFAULT_GANACHE_ADDR,
            ganache_port=DEFAULT_GANACHE_PORT,
            timeout: float = 2.0,
            max_attempts: int = 10)
```

Launch the Ganache image.

