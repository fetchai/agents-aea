# Car Park Detector

This agent sells information on the number of car parking spaces available in a given vicinity.

## Description

This agent is part of the Fetch.ai car park demo. It uses its primary skill, the `fetchai/carpark_detection` skill, to register its car park availability data selling service on the `SOEF`. It can then be contacted by another agent (for example the `fetchai/carpark_client` agent) to provide its data. 

Once such a request is made, this agent negotiates the terms of trade using the `fetchai/fipa` protocol, and if an agreement is reached, it delivers the data after receiving payment.

## Links

* <a href="https://docs.fetch.ai/aea/car-park-skills/" target="_blank">Car Park Demo</a>
