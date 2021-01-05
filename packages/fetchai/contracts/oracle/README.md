# Fetch Oracle Contract

## Description

This contract package is used to interface with a Fetch Oracle contract, which makes real-world data available to a smart-contract-capable blockchain.

## Functions

* `grantRole(oracle_role, oracle_address)`: grant oracle role to address `oracle_address`
* `updateOracleValue(value, decimals, txExpirationBlock)`: update oracle contract value to `value` with `decimals` decimal places, to expire at block `txExpirationBlock`