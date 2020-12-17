``` bash
aea fetch fetchai/tac_controller_contract:0.18.0
cd tac_controller_contract
aea install
```
``` bash
aea create tac_controller_contract
cd tac_controller_contract
aea add connection fetchai/p2p_libp2p:0.13.0
aea add connection fetchai/soef:0.14.0
aea add connection fetchai/ledger:0.11.0
aea add skill fetchai/tac_control_contract:0.15.0
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.13.0
aea config set agent.default_ledger ethereum
```
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```
``` bash
aea fetch fetchai/tac_participant:0.18.0 --alias tac_participant_one
cd tac_participant_one
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
cd ..
aea fetch fetchai/tac_participant:0.18.0 --alias tac_participant_two
cd tac_participant_two
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
```
``` bash
aea create tac_participant_one
aea create tac_participant_two
```
``` bash
cd tac_participant_one
aea add connection fetchai/p2p_libp2p:0.13.0
aea add connection fetchai/soef:0.14.0
aea add connection fetchai/ledger:0.11.0
aea add skill fetchai/tac_participation:0.14.0
aea add skill fetchai/tac_negotiation:0.16.0
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.13.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
```
``` bash
cd tac_participant_two
aea add connection fetchai/p2p_libp2p:0.13.0
aea add connection fetchai/soef:0.14.0
aea add connection fetchai/ledger:0.11.0
aea add skill fetchai/tac_participation:0.14.0
aea add skill fetchai/tac_negotiation:0.16.0
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea config set agent.default_connection fetchai/p2p_libp2p:0.13.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
```
``` bash
aea config get vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time
aea config set vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time '01 01 2020  00:01'
```
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat tac_controller_contract/ethereum_private_key.txt),1000000000000000000000" --account="$(cat tac_participant_one/ethereum_private_key.txt),1000000000000000000000" --account="$(cat tac_participant_two/ethereum_private_key.txt),1000000000000000000000"
```
``` bash
aea get-wealth ethereum
```
``` bash
aea launch tac_controller_contract tac_participant_one tac_participant_two
```
``` bash
aea delete tac_controller_contract
aea delete tac_participant_one
aea delete tac_participant_two
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
protocols: ['fetchai/oef_search:0.11.0', 'fetchai/fipa:0.11.0']
```