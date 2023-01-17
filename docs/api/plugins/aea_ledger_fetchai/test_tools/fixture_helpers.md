<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.fixture_helpers"></a>

# plugins.aea-ledger-fetchai.aea`_`ledger`_`fetchai.test`_`tools.fixture`_`helpers

Fixture helpers

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.fixture_helpers.fetchd"></a>

#### fetchd

```python
@pytest.fixture(scope="class")
def fetchd(fetchd_configuration=FETCHD_CONFIGURATION,
           timeout: float = 2.0,
           max_attempts: int = 20)
```

Launch the Fetch ledger image.

