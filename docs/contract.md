<a href="../api/contracts/base#contract-objects">`Contracts`</a> wrap smart contracts for Fetch.ai and third-party decentralized ledgers. In particular, they provide wrappers around the API or ABI of a smart contract and its byte code. They implement a translation between framework messages (in the `fetchai/contract_api:0.3.0` protocol) and the implementation specifics of the ABI.

Contracts usually implement four types of methods:

- a method to create a smart contract deployment transaction,
- methods to create transactions to modify state in the deployed smart contract,
- methods to create contract calls to execute static methods on the deployed smart contract, and
- methods to query the state of the deployed smart contract.

Contracts can be added as packages which means they become reusable across AEA projects.

The smart contract wrapped in a AEA contract package might be a third-party smart contract or your own smart contract potentially interacting with a third-party contract on-chain.


## Interacting with contracts from skills

Interacting with contracts in almost all cases requires network access. Therefore, the framework executes contract related logic in a <a href="../connection">Connection</a>.

In particular, the `fetchai/ledger:0.4.0` connection can be used to execute contract related logic. The skills communicate with the `fetchai/ledger:0.4.0` connection via the `fetchai/contract_api:0.3.0` protocol. This protocol implements a request-response pattern to serve the four types of methods listed above:

- the `get_deploy_transaction` message is used to request a deploy transaction for a specific contract. For instance, to request a deploy transaction for the deployment of the smart contract wrapped in the `fetchai/erc1155:0.9.0` package, we send the following message to the `fetchai/ledger:0.4.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.9.0",
    callable="get_deploy_transaction",
    kwargs=ContractApiMessage.Kwargs(
        {"deployer_address": self.context.agent_address}
    ),
)
```
This message will be handled by the `fetchai/ledger:0.4.0` connection and then a `raw_transaction` message will be returned with the matching raw transaction. To send this transaction to the ledger for processing, we first sign the message with the decision maker and then send the signed transaction to the `fetchai/ledger:0.4.0` connection using the `fetchai/ledger_api:0.3.0` protocol.

- the `get_raw_transaction` message is used to request any transaction for a specific contract which changes state in the contract. For instance, to request a transaction for the creation of token in the deployed `erc1155` smart contract wrapped in the `fetchai/erc1155:0.9.0` package, we send the following message to the `fetchai/ledger:0.4.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.9.0",
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
This message will be handled by the `fetchai/ledger:0.4.0` connection and then a `raw_transaction` message will be returned with the matching raw transaction. For this to be executed correctly, the `fetchai/erc1155:0.9.0` contract package needs to implement the `get_create_batch_transaction` method with the specified key word arguments. Similarly to above, to send this transaction to the ledger for processing, we first sign the message with the decision maker and then send the signed transaction to the `fetchai/ledger:0.4.0` connection using the `fetchai/ledger_api:0.3.0` protocol.

- the `get_raw_message` message is used to request any contract method call for a specific contract which does not change state in the contract. For instance, to request a call to get a hash from some input data in the deployed `erc1155` smart contract wrapped in the `fetchai/erc1155:0.9.0` package, we send the following message to the `fetchai/ledger:0.4.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.9.0",
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
This message will be handled by the `fetchai/ledger:0.4.0` connection and then a `raw_message` message will be returned with the matching raw message. For this to be executed correctly, the `fetchai/erc1155:0.9.0` contract package needs to implement the `get_hash_single` method with the specified key word arguments. We can then send the raw message to the `fetchai/ledger:0.4.0` connection using the `fetchai/ledger_api:0.3.0` protocol. In this case, signing is not required.


- the `get_state` message is used to request any contract method call to query state in the deployed contract. For instance, to request a call to get the balances in the deployed `erc1155` smart contract wrapped in the `fetchai/erc1155:0.9.0` package, we send the following message to the `fetchai/ledger:0.4.0`:

``` python
contract_api_msg = ContractApiMessage(
    performative=ContractApiMessage.Performative.GET_STATE,
    dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
    ledger_id=strategy.ledger_id,
    contract_id="fetchai/erc1155:0.9.0",
    contract_address=strategy.contract_address,
    callable="get_balance",
    kwargs=ContractApiMessage.Kwargs(
        {"agent_address": address, "token_id": token_id}
    ),
)
```
This message will be handled by the `fetchai/ledger:0.4.0` connection and then a `state` message will be returned with the matching state. For this to be executed correctly, the `fetchai/erc1155:0.9.0` contract package needs to implement the `get_balance` method with the specified key word arguments. We can then send the raw message to the `fetchai/ledger:0.4.0` connection using the `fetchai/ledger_api:0.3.0` protocol. In this case, signing is not required.


## Developing your own

The easiest way to get started developing your own contract is by using the <a href="../scaffolding">scaffold</a> command:

``` bash
aea scaffold contract my_new_contract
```

This will scaffold a contract package called `my_new_contract` with three files:

* `__init__.py` 
* `contract.py`, containing the scaffolded contract class
* `contract.yaml` containing the scaffolded configuration file

It helps to look at existing contract packages, like `fetchai/erc1155:0.9.0`, and skills using them, like `fetchai/erc1155_client:0.11.0` and `fetchai/erc1155_deploy:0.12.0`, for inspiration and guidance.
