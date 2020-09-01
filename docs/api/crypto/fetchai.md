<a name="aea.crypto.fetchai"></a>
# aea.crypto.fetchai

Fetchai module wrapping the public and private key cryptography and ledger api.

<a name="aea.crypto.fetchai.FetchAIHelper"></a>
## FetchAIHelper Objects

```python
class FetchAIHelper(CosmosHelper)
```

Helper class usable as Mixin for FetchAIApi or as standalone class.

<a name="aea.crypto.fetchai.FetchAICrypto"></a>
## FetchAICrypto Objects

```python
class FetchAICrypto(CosmosCrypto)
```

Class wrapping the Entity Generation from Fetch.AI ledger.

<a name="aea.crypto.fetchai.FetchAIApi"></a>
## FetchAIApi Objects

```python
class FetchAIApi(_CosmosApi,  FetchAIHelper)
```

Class to interact with the Fetch ledger APIs.

<a name="aea.crypto.fetchai.FetchAIApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize the Fetch.ai ledger APIs.

<a name="aea.crypto.fetchai.FetchAIFaucetApi"></a>
## FetchAIFaucetApi Objects

```python
class FetchAIFaucetApi(CosmosFaucetApi)
```

Fetchai testnet faucet API.

