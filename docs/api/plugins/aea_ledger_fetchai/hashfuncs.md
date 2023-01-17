<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.hashfuncs"></a>

# plugins.aea-ledger-fetchai.aea`_`ledger`_`fetchai.hashfuncs

Hash functions of Crypto package.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.hashfuncs.sha256"></a>

#### sha256

```python
def sha256(contents: bytes) -> bytes
```

Get sha256 hash.

**Arguments**:

- `contents`: bytes contents.

**Returns**:

bytes sha256 hash.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.hashfuncs.ripemd160"></a>

#### ripemd160

```python
def ripemd160(contents: bytes) -> bytes
```

Get ripemd160 hash using PyCryptodome.

**Arguments**:

- `contents`: bytes contents.

**Returns**:

bytes ripemd160 hash.

