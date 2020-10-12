# Generic Seller

A generic agent for selling data.

## Description

This agent uses its primary skill, the `fetchai/generic_seller` skill, to register its 'data-selling' service on the `SOEF`. It can then be contacted by another agent (for example the `fetchai/generic_buyer` agent) to provide specific data. 

Once such a request is made, this agent negotiates the terms of trade using the `fetchai/fipa` protocol, and if an agreement is reached, it delivers the data after receiving payment.

## Links

* <a href="https://docs.fetch.ai/aea/generic-skills/" target="_blank">Generic Skills</a>
* <a href="https://docs.fetch.ai/aea/generic-skills-step-by-step/" target="_blank">Generic Skill Step by Step Guide</a>
