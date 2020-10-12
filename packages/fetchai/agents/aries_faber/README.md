# Aries Faber

This agent represents the Faber actor in <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">this demo</a>.

## Description

This agent is part of the Fetch.ai Aries demo. It simulates the Faber actor of the demo linked above. It uses its primary skill, the `fetchai/aries_faber` skill, to do the following:
 * register a decentralised ID on a ledger
 * connects with an underlying aries cloud agent (ACA) instance, and forwards the following instructions:
    * register schema definition
    * register credential definition
    * create an invitation
 
It sends the invitation detail to an Alice agent that it finds via the `SOEF` service.

## Links

* <a href="https://docs.fetch.ai/aea/aries-cloud-agent-demo/" target="_blank">AEA Aries Demo</a>
* <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">Hyperledger Demo</a>
