# P2P stub connection

Simple file based connection to perform interaction between multiple local agents.

## Usage

First, add the connection to your AEA project: `aea add connection fetchai/p2p_stub:0.18.0`.

Optionally, in the `connection.yaml` file under `config` set the `namespace_dir` to the desired file path. The `p2p_stub` connection reads encoded envelopes from its input file and writes encoded envelopes to its output file. Multiple agents can be pointed to the same `namespace_dir` and are then able to exchange envelopes via the file system.
