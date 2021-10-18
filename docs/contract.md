<a href="../api/contracts/base#contract-objects">`Contracts`</a> wrap smart contracts for Fetch.ai and third-party decentralized ledgers. In particular, they provide wrappers around the API or ABI of a smart contract and its byte code. They implement a translation between framework messages (in the `fetchai/contract_api:1.0.0` protocol) and the implementation specifics of the ABI.

Contracts usually implement four types of methods:

- a method to create a smart contract deployment transaction,
- methods to create transactions to modify state in the deployed smart contract,
- methods to create contract calls to execute static methods on the deployed smart contract, and
- methods to query the state of the deployed smart contract.

Contracts can be added as packages which means they become reusable across AEA projects.

The smart contract wrapped in a AEA contract package might be a third-party smart contract or your own smart contract potentially interacting with a third-party contract on-chain.


## Interacting with contracts from skills

Interacting with contracts in almost all cases requires network access. Therefore, the framework executes contract related logic in a <a href="../connection">Connection</a>.

<img src="../assets/message-flow-contract-ledger.jpg" alt="Message flow for contract and ledger interactions" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

In particular, the `fetchai/ledger:0.19.0` connection can be used to execute contract related logic. The skills communicate with the `fetchai/ledger:0.19.0` connection via the `fetchai/contract_api:1.0.0` protocol. This protocol implements a request-response pattern to serve the four types of methods listed above:

- the `get_deploy_transaction` message is used to request a deploy transaction for a specific contract. For instance, to request a deploy transaction for the deployment of the smart contract wrapped in the `fetchai/erc1155:0.22.0` package, we send the following message to the `fetchai/ledger:0.19.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.22.0",
    callable="get_deploy_transaction",
    kwargs=ContractApiMessage.Kwargs(
        {"deployer_address": self.context.agent_address}
    ),
)
```

Any additional arguments needed by the contract's constructor method should be added to `kwargs`.

This message will be handled by the `fetchai/ledger:0.19.0` connection and then a `raw_transaction` message will be returned with the matching raw transaction. To send this transaction to the ledger for processing, we first sign the message with the decision maker and then send the signed transaction to the `fetchai/ledger:0.19.0` connection using the `fetchai/ledger_api:1.0.0` protocol. For details on how to implement the message handling, see the handlers in the `erc1155_deploy` skill.

<div class="admonition note">
  <p class="admonition-title">CosmWasm based smart contract deployments</p>
  <p>When using CosmWasm based smart contracts two types of deployment transactions exist. The first transaction stores the code on the chain. The second transaction initialises the code. This way, the same contract code can be initialised many times.<br>Both the <code>store</code> and <code>init</code> messages use the <code>ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION</code> performative. The ledger API automatically detects the type of transactions based on the provided keyword arguments. In particular, an <code>init</code> transaction requires the keyword arguments <code>code_id</code> (integer), <code>label</code> (string), <code>amount</code> (integer) and <code>init_msg</code> (JSON).<br>For an example look at the <code>fetchai/erc1155:0.22.0</code> package.
</p>
</div>

- the `get_raw_transaction` message is used to request any transaction for a specific contract which changes state in the contract. For instance, to request a transaction for the creation of token in the deployed `erc1155` smart contract wrapped in the `fetchai/erc1155:0.22.0` package, we send the following message to the `fetchai/ledger:0.19.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.22.0",
    contract_address=strategy.contract_address,
    callable="get_create_batch_transaction",
    kwargs=ContractApiMessage.Kwargs(
        {
            "deployer_address": self.context.agent_address,
            "token_ids": strategy.token_ids,
        }
    ),
)
```

This message will be handled by the `fetchai/ledger:0.19.0` connection and then a `raw_transaction` message will be returned with the matching raw transaction. For this to be executed correctly, the `fetchai/erc1155:0.22.0` contract package needs to implement the `get_create_batch_transaction` method with the specified key word arguments (see example in *Deploy your own*, below). Similarly to above, to send this transaction to the ledger for processing, we first sign the message with the decision maker and then send the signed transaction to the `fetchai/ledger:0.19.0` connection using the `fetchai/ledger_api:1.0.0` protocol.

- the `get_raw_message` message is used to request any contract method call for a specific contract which does not change state in the contract. For instance, to request a call to get a hash from some input data in the deployed `erc1155` smart contract wrapped in the `fetchai/erc1155:0.22.0` package, we send the following message to the `fetchai/ledger:0.19.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.22.0",
    contract_address=strategy.contract_address,
    callable="get_hash_single",
    kwargs=ContractApiMessage.Kwargs(
        {
            "from_address": from_address,
            "to_address": to_address,
            "token_id": token_id,
            "from_supply": from_supply,
            "to_supply": to_supply,
            "value": value,
            "trade_nonce": trade_nonce,
        }
    ),
)
```
This message will be handled by the `fetchai/ledger:0.19.0` connection and then a `raw_message` message will be returned with the matching raw message. For this to be executed correctly, the `fetchai/erc1155:0.22.0` contract package needs to implement the `get_hash_single` method with the specified key word arguments. We can then send the raw message to the `fetchai/ledger:0.19.0` connection using the `fetchai/ledger_api:1.0.0` protocol. In this case, signing is not required.


- the `get_state` message is used to request any contract method call to query state in the deployed contract. For instance, to request a call to get the balances in the deployed `erc1155` smart contract wrapped in the `fetchai/erc1155:0.22.0` package, we send the following message to the `fetchai/ledger:0.19.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_STATE,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.22.0",
    contract_address=strategy.contract_address,
    callable="get_balance",
    kwargs=ContractApiMessage.Kwargs(
        {"agent_address": address, "token_id": token_id}
    ),
)
```
This message will be handled by the `fetchai/ledger:0.19.0` connection and then a `state` message will be returned with the matching state. For this to be executed correctly, the `fetchai/erc1155:0.22.0` contract package needs to implement the `get_balance` method with the specified key word arguments. We can then send the raw message to the `fetchai/ledger:0.19.0` connection using the `fetchai/ledger_api:1.0.0` protocol. In this case, signing is not required.


## Developing your own

The easiest way to get started developing your own contract is by using the <a href="../scaffolding">scaffold</a> command:

``` bash
aea scaffold contract my_new_contract
```

This will scaffold a contract package called `my_new_contract` with three files:

* `__init__.py` 
* `contract.py`, containing the scaffolded contract class
* `contract.yaml` containing the scaffolded configuration file


Once your scaffold is in place, you can create a `build` folder in the package and copy the smart contract interface (e.g. bytes code and ABI) to it. Then, specify the path to the interfaces in the `contract.yaml`. For instance, if you use Ethereum, then you might specify the following:

``` yaml
contract_interface_paths:
    ethereum: build/my_contract.json
```
where `ethereum` is the ledger id and `my_contract.json` is the file containing the byte code and ABI.


Finally, you will want to implement the part of the contract interface you need in `contract.py`:

``` python
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


class MyContract(Contract):
    """The MyContract contract class which acts as a bridge between AEA framework and ERC1155 ABI."""

    @classmethod
    def get_create_batch_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        deployer_address: str,
        token_ids: List[int],
        data: Optional[bytes] = b"",
        gas: int = 300000,
    ) -> Dict[str, Any]:
        """
        Get the transaction to create a batch of tokens.

        :param ledger_api: the ledger API
        :param contract_address: the address of the contract
        :param deployer_address: the address of the deployer
        :param token_ids: the list of token ids for creation
        :param data: the data to include in the transaction
        :param gas: the gas to be used
        :return: the transaction object
        """
        # create the transaction dict
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        instance = cls.get_instance(ledger_api, contract_address)
        tx = instance.functions.createBatch(
            deployer_address, token_ids
        ).buildTransaction(
            {
                "gas": gas,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        tx = cls._try_estimate_gas(ledger_api, tx)
        return tx
```
Above, we implement a method to create a transaction, in this case a transaction to create a batch of tokens. The method will be called by the framework, specifically the `fetchai/ledger:0.19.0` connection once it receives a message (see bullet point 2 above). The method first gets the latest transaction nonce of the `deployer_address`, then constructs the contract instance, then uses the instance to build the transaction and finally updates the gas on the transaction.

It helps to look at existing contract packages, like `fetchai/erc1155:0.22.0`, and skills using them, like `fetchai/erc1155_client:0.11.0` and `fetchai/erc1155_deploy:0.30.0`, for inspiration and guidance.
