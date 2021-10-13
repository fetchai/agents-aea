# SOEF connection

The SOEF connection is used to connect to an SOEF node. The SOEF provides OEF services of register/unregister and search.

## Usage

First, add the connection to your AEA project: `aea add connection fetchai/soef:0.26.0`. Then ensure the `config` in `connection.yaml` matches your need. In particular, make sure `chain_identifier` matches your `default_ledger`.

To register/unregister services and perform searches use the `fetchai/oef_search:1.0.0` protocol