# Weather Station

This skill sells dummy weather data.

## Description

This skill is part of the Fetch.ai weather demo. It uses its primary skill, the `fetchai/weather_station` skill, to registers its 'weather-data-selling' service on the `SOEF`. This data comes from a database that is populated with dummy data from a weather station. 

Once such a request is made (for example by a `fetchai/weather_client` agent), this agent negotiates the terms of a deal using the `fetchai/fipa` protocol, and if an agreement is reached, it delivers the weather data after receiving payment.

## Links

* <a href="https://docs.fetch.ai/aea/weather-skills/" target="_blank">Weather Demo</a>
