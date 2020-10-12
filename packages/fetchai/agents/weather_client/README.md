# Weather Client

This agent buys dummy weather data.

## Description

This agent is part of the Fetch.ai weather demo. It uses its primary skill, the `fetchai/weather_client` skill, to find an agent selling weather data on the `SOEF` service. 

Once found, it requests weather data for specific dates, negotiates the price using the `fetchai/fipa` protocol, and if an agreement is reached, pays the proposed amount and receives the data.

## Links

* <a href="https://docs.fetch.ai/aea/weather-skills/" target="_blank">Weather Demo</a>