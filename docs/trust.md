AEA applications operate within different orders of _trustlessness_ or _trust minimisation_.

For example, using the AEA <a href="../weather-skills/">weather skills demo</a> without ledger payments means that clients must trust that any data the weather station sends is sufficient, including no data at all. Similarly, the weather station must trust the weather clients to send payment via some mechanism.

A step up, if you run the <a href="../weather-skills/">weather skills demo</a> with a ledger (e.g. Fetch.ai or Ethereum) then the clients must again trust the weather station to send sufficient data. However, all payment transactions are executed via the public ledger. This means the weather station no longer needs to trust the weather clients as it can observe the transactions taking place on the public ledger.

We can expand trustlessness even further by incorporating a third-party as an <a href="https://en.wikipedia.org/wiki/Escrow" target="_blank">arbitrator or escrow</a> implemented in a <a href="https://en.wikipedia.org/wiki/Smart_contract" target="_blank">smart contract</a>. However, in the weather skills demo there are limits to trustlessness as the station ultimately offers unverifiable data.

Finally, in the case of (non-fungible) token transactions where there is an atomic swap, trustlessness is apparent (e.g. in the <a href="../tac-skills-contract/">TAC demo</a>).

<br />
