The 'Open Economic Framework' (OEF) is a node that enables us to search, discover and communicate with possible clients or services. 
For the AEAs to be able to find each other, one must register as a service and the other must query the OEF node for a service. 

Currently, you need to run your own OEF node for local development and testing.

To start an OEF node follow the <a href="../quickstart/#preliminaries">Preliminaries</a> sections from the AEA quick start. Then run:

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

We will soon make a public OEF network available.


Ledgers enable the AEAs to complete a transaction and transfer funds to each other. Another way the AEA framework uses 
the ledgers are to interact with smart contracts.

In the AEA framework universe, agents register in a search and discovery service (OEF) that enables the agents to find each other and can use the ledger to complete transactions. The following diagram illustrates the relation to the OEF and a Ledger.


<center>![The AEA, OEF, and Ledger systems](assets/oef-ledger.png)</center>