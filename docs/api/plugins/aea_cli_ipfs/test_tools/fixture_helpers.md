<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.test_tools.fixture_helpers"></a>

# plugins.aea-cli-ipfs.aea`_`cli`_`ipfs.test`_`tools.fixture`_`helpers

Fixture helpers.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.test_tools.fixture_helpers.ipfs_daemon"></a>

#### ipfs`_`daemon

```python
@pytest.fixture(scope="module")
def ipfs_daemon() -> Iterator[bool]
```

Starts an IPFS daemon for the tests.

