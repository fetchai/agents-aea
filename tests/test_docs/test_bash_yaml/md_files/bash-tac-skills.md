``` bash
{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9001"
}
```
``` bash
{
  "delegate_uri": "127.0.0.1:11002",
  "entry_peers": ["REPLACE_WITH_MULTI_ADDRESS_HERE"],
  "local_uri": "127.0.0.1:9002",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:9002"
}
```
``` bash
aea fetch fetchai/tac_controller:0.29.0
cd tac_controller
aea install
aea build
```
``` bash
aea create tac_controller
cd tac_controller
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/tac_control:0.24.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_ledger fetchai
aea config set --type dict agent.default_routing \
'{
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea install
aea build
```
``` bash
aea fetch fetchai/tac_participant:0.31.0 --alias tac_participant_one
cd tac_participant_one
aea install
aea build
cd ..
aea fetch fetchai/tac_participant:0.31.0 --alias tac_participant_two
cd tac_participant_two
aea build
```
``` bash
aea create tac_participant_one
aea create tac_participant_two
```
``` bash
cd tac_participant_one
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/tac_participation:0.24.0
aea add skill fetchai/tac_negotiation:0.28.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_ledger fetchai
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea install
aea build
```
``` bash
cd tac_participant_two
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/tac_participation:0.24.0
aea add skill fetchai/tac_negotiation:0.28.0
aea config set --type dict agent.dependencies \
'{
  "aea-ledger-fetchai": {"version": "<2.0.0,>=1.0.0"}
}'
aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea config set agent.default_ledger fetchai
aea config set --type dict agent.default_routing \
'{
  "fetchai/ledger_api:1.0.0": "fetchai/ledger:0.19.0",
  "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0"
}'
aea config set --type dict agent.decision_maker_handler \
'{
  "dotted_path": "aea.decision_maker.gop:DecisionMakerHandler",
  "file_path": null
}'
aea install
aea build
```
``` bash
aea generate-key fetchai
aea add-key fetchai fetchai_private_key.txt
```
``` bash
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
``` bash
aea config get vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time '01 01 2020  00:01'
```
``` bash
aea config set vendor.fetchai.skills.tac_control.models.parameters.args.registration_start_time "$(date -d "2 minutes" +'%d %m %Y %H:%M')"
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
aea run
```
``` bash
aea launch tac_participant_one tac_participant_two
```
``` bash
aea delete tac_controller
aea delete tac_participant_one
aea delete tac_participant_two
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.25.0
type: connection
config:
  delegate_uri: 127.0.0.1:11001
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9001
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9001
```
``` yaml
---
public_id: fetchai/p2p_libp2p:0.25.0
type: connection
config:
  delegate_uri: 127.0.0.1:11002
  entry_peers: ['SOME_ADDRESS']
  local_uri: 127.0.0.1:9002
  log_file: libp2p_node.log
  public_uri: 127.0.0.1:9002
```