AEA applications operate within different orders of trustlessness.

For example, using the AEA weather skills demo without a ledger means that clients must trust that any data the weather station sends is sufficient, including no data at all. Similarly, the weather station must trust the weather clients to send payment via some mechanism.

A step up, if you run the weather skills demo with a ledger (Fetch.ai or Ethereum) then the clients must again trust the weather station to send sufficient data. However, all payment transactions are executed via the public ledger. This means the weather station no longer needs to trust the weather clients as it can observe the transactions taking place on the public ledger.

We can expand trustlessness even further by incorporating a third party as an arbitrator or some escrow contract. However, in the weather skills demo there are limits to trustlessness as the station ultimately offers unverifiable data.

Finally, in the case of (non-fungible) token transactions where there is an atomic swap, full trustlessness is apparent. This is demonstrated in the TAC.


<br />
