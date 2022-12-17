While developing AEAs, users frequently face the need of interacting with smart contracts in a third-party decentralized ledger. To achieve this, developers must create <a href="../contract">Contract</a> packages: components that provide wrappers around the API or ABI of the target smart contract.

In this guide, we will learn how to develop our own contract package to interface with an ERC20 token. We will use the WETH contract deployed on Ethereum <a href="https://etherscan.io/token/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2#readContract" target="_blank">at this address</a>.

## Step-by-step instructions

Before starting this guide, ensure that you have done one of the following things:

- You have cloned our <a href="https://github.com/valory-xyz/dev-template" target="_blank">developer template</a>. Once setup, it will generate a virtual environment with Open AEA installed, an empty local registry, some useful tools for checking packages and dummy tests.

- You have gone through the <a href="https://open-aea.docs.autonolas.tech/quickstart/" target="_blank">quickstart</a> to verify that your machine satisfies the framework requirements and that you have followed the setup instructions so you have the Open AEA framework and the Ethereum plugin installed.

Now, let's create our contract package:

1. Download the WETH contract ABI <a href="https://etherscan.io/token/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2#code" target="_blank">here</a>: scroll down to the **Contract ABI** section and click the **copy** button on the right. Then, create a new file called `IERC20.json` and paste the content you have just copied there.

2. Initialize the IPFS registry:
```bash
autonomy init --reset --author john_doe --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"
```

3. Scaffold the ERC20 contract:
```bash
aea scaffold --to-local-registry contract ERC20Contract /path/to/IERC20.json
```
You'll find the contract in the local registry at `packages/john_doe/contracts/ERC20Contract`.


4. Now it is time to call the new method from an agent. Let's say that we would like to get the WETH balance for the WETH account itself. In any skill's `behaviour.py` file, first import the contract package and set the target address:
```python
from packages.john_doe.contracts.erc20.contract import (
    ContractApiMessage,
)

WETH_ADDRESS = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
```

    And finally, call the get_balance method from any behaviour:
```python
contract_api_msg = yield from self.get_contract_api_response(
    performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
    contract_address=WETH_ADDRESS,
    contract_id=str(ERC20Contract.contract_id),
    contract_callable="balanceOf",
    address=WETH_ADDRESS,
)

if contract_api_msg.performative != ContractApiMessage.Performative.STATE:
    self.context.logger.info("Error retrieving the balance")
    return

balance = contract_api_msg.state.body
```

At some point we might need to have some custom implementation in our contract package methods. For those cases, proceed as follows:

1. Open the contract at `packages/john_doe/contracts/ERC20Contract/contract.py` and add the following imports at the top of the file:
```python
from aea_ledger_ethereum import EthereumApi
from typing import Optional
```

    Also add a custom method to retrieve balances to the `ERC20Contract` class
```python
    @classmethod
    def balance_of(
        cls, ledger_api: EthereumApi, contract_address: str, owner_address: str
    ) -> Optional[JSONLike]:
        """Gets an account's balance."""
        contract_instance = cls.get_instance(ledger_api, contract_address)

        # Implement your custom logic here. This is just an example:
        return ledger_api.contract_method_call(
            contract_instance=contract_instance,
            method_name="balanceOf",
            owner=owner_address,
        )
```

2. Fingerprint the contract so its hash matches our changes:
```bash
aea packages lock
```

3. Proceed with the call as we did previously.