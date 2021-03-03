# Aries Alice

## Description

This skill emulates the Alice actor in <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">this demo</a>.

This skill is part of the Fetch.ai Aries demo. It simulates the Alice actor of the demo linked above. It first registers Alice on the sOEF. It then receives invitation details from Faber AEA. Then it connects with an underlying Aries cloud agent (ACA) instance and executes an `accept-invitation` command.

## Behaviours

* `alice`: registers and unregisters Alice AEA on the sOEF

## Handlers

* `default`: handles `default` messages for the invitation detail it receives from the Faber AEA
* `http`: handles `http` messages for communicating with Alice ACA
* `oef_search`: handles `oef_search` messages if registration on the sOEF was erratic

## Links

* <a href="https://docs.fetch.ai/aea/aries-cloud-agent-demo/" target="_blank">AEA Aries Demo</a>
* <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target="_blank">Hyperledger Demo</a>
