# Aries Faber

## Description

This skill emulates the Faber actor in <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">this demo</a>.

This skill is part of the Fetch.ai Aries demo. It simulates the Faber actor of the demo linked above. It first registers a decentralised ID on an underlying ledger. It then connects with an underlying Aries cloud agent (ACA) instance, and forwards the following instructions:
 * register schema definition
 * register credential definition
 * create an invitation
 
It then sends the invitation detail to an Alice agent that it finds via the sOEF.

## Behaviours

* `faber`: searches for Alice AEA 

## Handlers

* `http`: handles `http` messages for communicating with the ledger and Faber ACA
* `oef_search`: handles `oef_search` messages of finding Alice on the sOEF

## Links

* <a href="https://docs.fetch.ai/aea/aries-cloud-agent-demo/" target="_blank">AEA Aries Demo</a>
* <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">Hyperledger Demo</a>
