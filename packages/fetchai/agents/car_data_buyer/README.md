# Car Park Client

This agent purchases information on available car parking spaces in a vicinity.

## Description

This agent is part of the Fetch.ai car park demo. It uses its primary skill, the `fetchai/carpark_client` skill, to find an agent on the `SOEF` service that sells car park availability data in a vicinity. 

Once found, it requests this data, negotiates the price using the `fetchai/fipa` protocol, and if an agreement is reached, pays the proposed amount and receives the data. 

## Links

* <a href="https://docs.fetch.ai/aea/car-park-skills/" target="_blank">Car Park Demo</a>
