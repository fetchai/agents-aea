# Fetch ERC1155 Contract

## Description

This contract package is used to interface with an ERC1155 smart contract.

## Functions

* `generate_token_ids(token_type, nb_tokens, starting_index)`: Generate token ids.
* `get_create_batch_transaction(token_ids)`: Get the transaction to create a batch of `token_ids` tokens.
* `get_create_single_transaction()`: Get the transaction to create a single `token_id` token.
* `get_mint_batch_transaction(token_ids, mint_quantities)`: Get the transaction to mint `mint_quantities` number of `token_ids` tokens.
* `validate_mint_quantities(token_ids, mint_quantities)`: Validate the mint quantities
* `get_mint_single_transaction(token_id, mint_quantity)`: Get the transaction to mint `mint_quantity` number of a single `token_id` token.
* `get_balance(token_id)`: Get the balance for a specific `token_id`.
* `get_atomic_swap_single_transaction(token_id)`: Get the transaction for a trustless trade between two agents for a single `token_id` token.
* `get_balances(token_ids)`: Get the balances for a batch of specific `token_ids`.
* `get_atomic_swap_batch_transaction(token_ids)`: Get the transaction for a trustless trade between two agents for a batch of `token_ids` tokens.
* `get_hash_single(token_id)`: Get the hash for a trustless trade between two agents for a single `token_id` token.
* `get_hash_batch(token_ids)`: Get the hash for a trustless trade between two agents for a batch of `token_ids` token.
* `generate_trade_nonce()`: Generate a valid trade nonce.


## Links

* <a href="https://eips.ethereum.org/EIPS/eip-1155" target="_blank">ERC1155 Standard</a>
