# Ledger connection

The ledger connection wraps the APIs needed to interact with multiple ledgers, including smart contracts deployed on those ledgers.

The AEA communicates with the ledger connection via the `fetchai/ledger_api:0.8.0` and `fetchai/contract_api:0.9.0` protocols.

The connection uses the ledger apis registered in the ledger api registry.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/ledger:0.11.0`). Optionally, update the `ledger_apis` in `config` of `connection.yaml`.
