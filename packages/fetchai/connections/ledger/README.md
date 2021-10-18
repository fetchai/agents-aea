# Ledger connection

The ledger connection wraps the APIs needed to interact with multiple ledgers, including smart contracts deployed on those ledgers.

The AEA communicates with the ledger connection via the `fetchai/ledger_api:1.0.0` and `fetchai/contract_api:1.0.0` protocols.

The connection uses the ledger APIs registered in the ledger API registry.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/ledger:0.19.0`). Optionally, update the `ledger_apis` in `config` of `connection.yaml`.
