<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This section is highly experimental. We will update it soon.</p>
</div>

The `fetchai/p2p_noise:0.1.0` connection allows AEAs to create a peer-to-peer communication network. In particular, the connection creates an overlay network which maps agents' public keys to IP addresses.

## Local Demo

### Create and run the genesis AEA

Create one AEA as follows:

``` bash
aea create my_genesis_aea
cd my_genesis_aea
aea add connection fetchai/p2p_noise:0.1.0
aea config set agent.default_connection fetchai/p2p_noise:0.1.0
aea run --connections fetchai/p2p_noise:0.1.0
```

### Create and run another AEA

Create a second AEA:

``` bash
aea create my_other_aea
cd my_other_aea
aea add connection fetchai/p2p_noise:0.1.0
aea config set agent.default_connection fetchai/p2p_noise:0.1.0
```

Provide the AEA with the information it needs to find the genesis by adding the following block to `vendor/fetchai/connnections/p2p_noise/connection.yaml`:

``` yaml
config:
  noise_entry_peers: ["127.0.0.1:9000"]
  noise_host: 127.0.0.1
  noise_log_file: noise_node.log
  noise_port: 9001
```

Run the AEA:

``` bash
aea run --connections fetchai/p2p_noise:0.1.0
```

You can inspect the `noise_node.log` log files of the AEA to see how they discover each other.

## Deployed Test Network

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Coming soon.</p>
</div>