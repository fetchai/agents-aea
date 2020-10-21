# Thermometer Client

This agent buys thermometer data.

## Description

This agent is part of the Fetch.ai thermometer demo. It uses its primary skill, the `fetchai/thermometer_client` skill, to find an agent selling thermometer data on the `SOEF` service. 

Once found, it requests data from a thermometer reading, negotiates the price using the `fetchai/fipa` protocol, and if an agreement is reached, pays the proposed amount and receives the data.

## Links

* <a href="https://docs.fetch.ai/aea/thermometer-skills/" target="_blank">Thermometer Demo</a>
