# Coin Price Feed AEA

An agent that fetches a coin price from an API and makes it available by http request. 

## Description

This agent uses the `fetchai/advanced_data_request` skill to fetch a coin price from an API, which is then logged and then made available by http request using the `fetchai/http_server` connection. The agent also exposes the number of price quote retrievals and incoming http requests to a local prometheus server.
