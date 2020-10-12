# Aries Faber

This agent represents the Faber actor in <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">this demo</a>.

## Description

This agent is part of the Fetch.ai Aries demo. It simulates the Faber actor of the demo linked above. It uses its primary skill, the `fetchai/aries_faber` skill, to do the following:
 * Register a decentralised ID on a ledger.
 * Connects with an underlying Aries Cloud Agent (ACA) instance, and forwards the following instructions:
    * Register schema definition
    * Register credential definition
    * Create an invitation
 
It then sends the invitation detail to the Alice agent (see `fetchai/aries_alice` agent) it finds via the `SOEF` service.

## Links

* <a href="https://docs.fetch.ai/aea/aries-cloud-agent-demo/" target="_blank">AEA Aries Demo</a>
* <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">Hyperledger Demo</a>
