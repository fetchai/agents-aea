``` bash
aea fetch fetchai/tac_controller_contract:0.23.0
cd tac_controller_contract
aea install
aea build
```
``` bash
aea create tac_controller_contract
cd tac_controller_contract
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/tac_control_contract:0.19.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
aea config set --type bool vendor.fetchai.skills.tac_control.is_abstract true
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea install
aea build
```
``` bash
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
```
``` bash
aea fetch fetchai/tac_participant:0.23.0 --alias tac_participant_one
cd tac_participant_one
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
cd ..
aea fetch fetchai/tac_participant:0.23.0 --alias tac_participant_two
cd tac_participant_two
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
```
``` bash
aea create tac_participant_one
aea create tac_participant_two
```
``` bash
cd tac_participant_one
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/tac_participation:0.18.0
aea add skill fetchai/tac_negotiation:0.21.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
```
``` bash
cd tac_participant_two
aea add connection fetchai/p2p_libp2p:0.17.0
aea add connection fetchai/soef:0.18.0
aea add connection fetchai/ledger:0.14.0
aea add skill fetchai/tac_participation:0.18.0
aea add skill fetchai/tac_negotiation:0.21.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<0.2.0,>=0.1.0"},
  "aea-ledger-ethereum": {"version": "<0.2.0,>=0.1.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.17.0
aea config set agent.default_ledger ethereum
aea config set vendor.fetchai.connections.soef.config.chain_identifier ethereum
aea config set vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract 'True' --type bool
aea config set vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx 'True' --type bool
aea config set --type dict agent.default_routing \
'{
  "fetchai/contract_api:0.12.0": "fetchai/ledger:0.14.0",
  "fetchai/ledger_api:0.11.0": "fetchai/ledger:0.14.0",
  "fetchai/oef_search:0.14.0": "fetchai/soef:0.18.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "ethereum", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "save_path": ".certs/conn_cert.txt"}]'
aea generate-key ethereum
aea add-key ethereum ethereum_private_key.txt
aea install
aea build
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea config get vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time
aea config set vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time '01 01 2020  00:01'
```
``` bash
aea config set vendor.fetchai.skills.tac_control_contract.models.parameters.args.registration_start_time "$(date -d "2 minutes" +'%d %m %Y %H:%M')"
```
``` bash
aea run
```
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}'
```
``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11002",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:9002",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9002"
}'
```
``` bash
docker run -p 8545:8545 trufflesuite/ganache-cli:latest --verbose --gasPrice=0 --gasLimit=0x1fffffffffffff --account="$(cat tac_controller_contract/ethereum_private_key.txt),1000000000000000000000" --account="$(cat tac_participant_one/ethereum_private_key.txt),1000000000000000000000" --account="$(cat tac_participant_two/ethereum_private_key.txt),1000000000000000000000"
```
``` bash
aea get-wealth ethereum
```
``` bash
aea run tac_contract_controller
```
``` bash
aea launch tac_participant_one tac_participant_two
```
``` bash
aea delete tac_controller_contract
aea delete tac_participant_one
aea delete tac_participant_two
```