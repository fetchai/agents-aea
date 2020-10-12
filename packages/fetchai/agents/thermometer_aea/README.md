# Thermometer

This agent sells thermometer data.

## Description

This agent is part of the Fetch.ai thermometer demo. It uses its primary skill, the `fetchai/thermometer` skill, to register its 'thermometer-data-selling' service on the `SOEF`. 

It can be contacted by another agent (for example the `fetchai/thermometer_client` agent) to provide data from a thermometer reading. 

Once such a request is made, this agent negotiates the terms of trade using the `fetchai/fipa` protocol, and if an agreement is reached, it reads data from a (real or fake) thermometer, and delivers it after receiving payment.

## Links

* <a href="https://docs.fetch.ai/aea/thermometer-skills/" target="_blank">Thermometer Demo</a>
