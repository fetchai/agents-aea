``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```
``` bash
aea create tac_controller
cd tac_controller
```
``` bash
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/tac_control:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.start_time
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.start_time '01 01 2020  00:01'
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
``` bash
aea create tac_participant_one
aea create tac_participant_two
```
``` bash
cd tac_participant_one
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/tac_participation:0.1.0
aea add skill fetchai/tac_negotiation:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
cd tac_participant_two
aea add connection fetchai/oef:0.2.0
aea add skill fetchai/tac_participation:0.1.0
aea add skill fetchai/tac_negotiation:0.1.0
aea add contract fetchai/erc1155:0.1.0
aea install
aea config set agent.default_connection fetchai/oef:0.2.0
```
``` bash
aea config set agent.default_ledger ethereum
```
``` bash
aea run --connections fetchai/oef:0.2.0
```
```bash
aea launch tac_controller tac_participant_one tac_participant_two
```
``` bash
aea fetch fetchai/tac_controller:0.1.0
aea fetch fetchai/tac_participant:0.1.0
```
``` yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 20
```
``` yaml
name: tac_negotiation
authors: fetchai
version: 0.1.0
license: Apache-2.0
description: "The tac negotiation skill implements the logic for an AEA to do fipa negotiation in the TAC."
behaviours:
  behaviour:
      class_name: GoodsRegisterAndSearchBehaviour
      args:
        services_interval: 5
  clean_up:
    class_name: TransactionCleanUpBehaviour
    args:
      tick_interval: 5.0
handlers:
  fipa:
    class_name: FIPANegotiationHandler
    args: {}
  transaction:
    class_name: TransactionHandler
    args: {}
  oef:
    class_name: OEFSearchHandler
    args: {}
models:
  search:
    class_name: Search
    args:
      search_interval: 5
  registration:
    class_name: Registration
    args:
      update_interval: 5
  strategy:
    class_name: Strategy
    args:
      register_as: both
      search_for: both
  dialogues:
    class_name: Dialogues
    args: {}
  transactions:
    class_name: Transactions
    args:
      pending_transaction_timeout: 30
protocols: ['fetchai/oef_search:0.1.0', 'fetchai/fipa:0.1.0']
```
