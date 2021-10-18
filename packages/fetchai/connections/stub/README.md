# Stub connection
A simple connection for communication with an AEA, using the file system as a point of data exchange.

## Usage
First, add the connection to your AEA project: `aea add connection fetchai/stub:0.21.0`. (If you have created your AEA project with `aea create` then the connection will already be available by default.)

Optionally, in the `connection.yaml` file under `config` set the `input_file` and `output_file` to the desired file path. The `stub` connection reads encoded envelopes from the `input_file` and writes encoded envelopes to the `output_file`.
