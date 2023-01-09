## Ledgers

Ledgers enable AEAs to store transactions, for example involving the transfer of funds to each other, or the execution of smart contracts. They optionally ensure the truth and integrity of agent to agent interactions.

Whilst a ledger can, in principle, be used to store structured data (for instance, training data in a machine learning model) in most use cases the resulting costs and privacy implications do not make this an efficient use of the ledger. Instead, usually only references to structured data - often in the form of hashes - are stored on a ledger, and the actual data is stored off-chain.

The Python implementation of the AEA Framework currently integrates with three ledgers:

- <a href="https://docs.fetch.ai/ledger/" target="_blank">Fetch.ai ledger</a>
- <a href="https://ethereum.org/en/developers/learning-tools/" target="_blank">Ethereum ledger</a>
- <a href="https://v1.cosmos.network/sdk" target="_blank">Cosmos ledger</a>

However, the framework makes it straightforward for any developer to add support for other ledgers.

### AEAs as second layer technology

The following presentation discusses how AEAs can be seen as second layer technology to ledgers.

<iframe width="560" height="315" src="https://www.youtube.com/embed/gvzYX7CYk-A" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
