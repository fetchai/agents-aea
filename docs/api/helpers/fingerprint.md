<a id="aea.helpers.fingerprint"></a>

# aea.helpers.fingerprint

Helper tools for fingerprinting packages.

<a id="aea.helpers.fingerprint.compute_fingerprint"></a>

#### compute`_`fingerprint

```python
def compute_fingerprint(
        package_path: Path,
        fingerprint_ignore_patterns: Optional[Collection[str]]
) -> Dict[str, str]
```

Compute the fingerprint of a package.

**Arguments**:

- `package_path`: path to the package.
- `fingerprint_ignore_patterns`: filename patterns whose matches will be ignored.

**Returns**:

the fingerprint

<a id="aea.helpers.fingerprint.update_fingerprint"></a>

#### update`_`fingerprint

```python
def update_fingerprint(configuration: PackageConfiguration) -> None
```

Update the fingerprint of a package.

**Arguments**:

- `configuration`: the configuration object.

<a id="aea.helpers.fingerprint.check_fingerprint"></a>

#### check`_`fingerprint

```python
def check_fingerprint(configuration: PackageConfiguration) -> bool
```

Check the fingerprint of a package, given the loaded configuration file.

**Arguments**:

- `configuration`: the configuration object.

**Returns**:

True if the fingerprint match, False otherwise.

