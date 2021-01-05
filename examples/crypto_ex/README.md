# Crypto plug-in example

This example contains a custom crypto
package to be used by the AEA.

Install the package:
```
pip install -e .
```

Then, open a Python interpreter and run:

```
import aea
from aea.crypto.registries import make_crypto

my_crypto_object = make_crypto("my_crypto")
```