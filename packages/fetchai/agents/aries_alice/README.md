# Aries Alice

This agent represents the Alice actor in <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">this demo</a>.

## Description

This agent is part of the Fetch.ai Aries demo. It simulates the Alice actor of the demo linked above. It uses its primary skill, the `fetchai/aries_alice` skill, to do the following:

* Registers Alice on the `SOEF` service. 
* On receiving an invitation details from Faber AEA (see `fetchai/aries_faber` agent), it connects with an underlying Aries Cloud Agent (ACA) instance and executes an `accept-invitation` command.

## Links

* <a href="https://docs.fetch.ai/aea/aries-cloud-agent-demo/" target="_blank">AEA Aries Demo</a>
* <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">Hyperledger Demo</a>
