# Gym connection

Connection providing access to the gym interface (https://github.com/openai/gym) for training reinforcement learning systems.

The connection wraps a gym and allows the AEA to interact with the gym interface via the `gym` protocol.

## Usage

First, add the connection to your AEA project (`aea add connection fetchai/gym:0.19.0`). Then, update the `config` in `connection.yaml` by providing a dotted path to the gym module in the `env` field.
