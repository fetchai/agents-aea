``` bash 
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
```
``` bash
rustup default stable
cargo version
# If this is lower than 1.44.1+, update with:
# rustup update stable

rustup target list --installed
rustup target add wasm32-unknown-unknown
```
``` bash
git clone https://github.com/fetchai/fetchd.git
cd fetchd
git checkout release/v0.2.x
make install

# Check if wasmcli is properly installed
wasmcli version
# Version should be >=0.2.5
```
``` bash
wasmcli config chain-id agent-land
wasmcli config trust-node false
wasmcli config node https://rpc-agent-land.fetch.ai:443
wasmcli config output json
wasmcli config indent true
wasmcli config broadcast-mode block
```
