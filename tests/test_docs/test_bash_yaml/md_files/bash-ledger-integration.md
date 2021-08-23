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
git checkout release/v0.8.x
make install
