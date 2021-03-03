
## Measuring runtime cost

It is important to emphasise the fact that the AEA is a framework, so ultimately its running cost will highly depend on the number and type of components which are being run as part of a given AEA. The other cost factor is determined by the cost of running the core framework itself and how fast and efficient the framework is in interconnecting the components.

These observations can provide guidance on what to report as part of the cost of running an AEA.

Here is a list of suggestion on how to measure the cost of running an AEA:
- the cost of running the framework itself: by running a minimal agent with an idle loop (the default one) with no connections, skills or protocols and measuring memory usage and CPU consumption as a baseline.
- the cost of interconnecting components: by running an a agent with a basic skill (e.g. `fetchai/echo`) and measuring memory usage and CPU consumption relative to number of messages exchanged as well as bandwidth.
- the cost of basic components: dialogues memory relative to number of messages, SOEF connection baseline memory usage, P2P connection baseline memory usage, smart contract baseline memory usage

The `aea run --profiling SECONDS` command can be used to report measures in all of the above scenarios.
