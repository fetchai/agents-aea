# ML Train

This agent buys ML data for training.

## Description

This skill is part of the Fetch.ai ML skill demo. It uses its primary skill, the `fetchai/ml_train` skill, to find an agent selling ML data on the `SOEF` service (for example a `fetchai/ml_data_provider` agent). 

Once found, it requests specific data samples. If both parties agree with the terms of trade, it pays the proposed amount and trains an ML model using the data bought.

## Links

* <a href="https://docs.fetch.ai/aea/ml-skills/" target="_blank">ML Demo</a>