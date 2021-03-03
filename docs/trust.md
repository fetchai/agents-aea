AEA applications have different requirements for _trustlessness_ or _trust minimisation_.

For example, using the AEA <a href="../weather-skills/">weather skills demo</a> _without_ ledger payments means that the client has to trust the weather station to send the weather data it purchased and that this data is in fact valid. Similarly, the weather station must trust that the client somehow sends the payment amount to which they agreed.

A step up, if you run the <a href="../weather-skills/">weather skills demo</a> with a ledger (e.g. Fetch.ai or Ethereum) then the client must still trust that the weather station sends valid data. However, all payment transactions are executed via the public ledger. This means the weather station no longer needs to trust the client for payment and can verify whether the transactions take place on the public ledger.

We can further minimise trust requirements by incorporating a third party as an <a href="https://en.wikipedia.org/wiki/Escrow" target="_blank">arbitrator or escrow</a> implemented in a <a href="https://en.wikipedia.org/wiki/Smart_contract" target="_blank">smart contract</a> to further reduce trust requirements. However, in the current weather skills demo, there are limits to trustlessness as the station ultimately offers unverifiable data.

Another example of minimising trust, is applications with (non-fungible) token transactions involving <a href="https://dl.acm.org/doi/10.1145/3212734.3212736" target="_blank">atomic swaps</a> where trustlessness is clearly satisfied (e.g. in the <a href="../tac-skills-contract/">TAC demo</a>).

<br />
