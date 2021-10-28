This demo shows how AEAs can aggregate values over the peer-to-peer network.

## Discussion

This demonstration shows how to set up a simple aggregation network in which several AEAs take an average of values fetched from different sources for the same real-world quantity. For this particular example, we take an average of Bitcoin prices from four public APIs.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## Demo

### Create the AEAs

Repeat the following process four times in four different terminals (for each {`i=0`, `i=1`, `i=2`, `i=3`}):

Fetch the aggregator AEA:
``` bash
agent_name="agg$i"
aea fetch fetchai/simple_aggregator:0.4.0 --alias $agent_name
cd $agent_name
aea install
aea build
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

Create the AEA.

``` bash
agent_name="agg$i"
aea create agent_name
cd agent_name
aea add connection fetchai/http_client:0.23.0
aea add connection fetchai/http_server:0.22.0
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/prometheus:0.8.0
aea add skill fetchai/advanced_data_request:0.6.0
aea add skill fetchai/simple_aggregation:0.2.0

aea config set agent.default_connection fetchai/p2p_libp2p:0.25.0
aea install
aea build
```

Set the desired decimal precision for the quantity:
``` bash
aea config set --type int vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.decimals 0
```

Disable the http server since it is not used in this demo:
``` bash
aea config set --type bool vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.use_http_server false
```

</p>
</details>


Set the cert requests for the peer-to-peer connection:
``` bash
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "fetchai", "not_after": "2022-01-01", "not_before": "2021-01-01", "public_key": "fetchai", "message_format": "{public_key}", "save_path": ".certs/conn_cert.txt"}]'
```

Match the agent index `i` to the `COIN_URL` and `JSON_PATH` below:
- `agg0`: `COIN_URL="https://api.coinbase.com/v2/prices/BTC-USD/buy" && JSON_PATH="data.amount"`
- `agg1`: `COIN_URL="https://api.coinpaprika.com/v1/tickers/btc-bitcoin" && JSON_PATH="quotes.USD.price"`
- `agg2`: `COIN_URL="https://api.cryptowat.ch/markets/kraken/btcusd/price" && JSON_PATH="result.price"`
- `agg3`: `COIN_URL="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd" && JSON_PATH="bitcoin.usd"`

Set the following configuration for the `advanced_data_request` skill:
``` bash
aea config set vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url $COIN_URL
aea config set vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs '[{"name": "price", "json_path": '"\"$JSON_PATH\""'}]'
```

Set the name of the quantity to aggregate and choose an aggregation function for the AEAs (the currently implemented options are `mean`, `median`, and `mode`):
``` bash
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.quantity_name price
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.aggregation_function mean
```

Specify a name for your aggregation service:
``` bash
SERVICE_ID=my_btc_aggregation_service
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.service_id $SERVICE_ID
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.search_query.search_value $SERVICE_ID
```

Additionally, create private keys for use with the ledger and the peer-to-peer connection:
``` bash
aea generate-key fetchai
aea add-key fetchai
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```

Finally, certify the keys for use by the connections that request them:
``` bash
aea issue-certificates
```

### Configure the peer-to-peer network

Set the multi-address of the first AEA as an initial peer to help the remaining AEAs find each other on the network. Also, if these AEAs are all running on the same machine, set different ports for their connections to ensure there are no conflicts (from the `agg1`, `agg2`, and `agg3` directories):
``` bash
MULTIADDR=$(cd ../agg0 && aea get-multiaddress fetchai --connection)
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
"delegate_uri": "127.0.0.1:'$((11000+i))'",
"entry_peers": ["/dns4/127.0.0.1/tcp/9000/p2p/'"$MULTIADDR\""'],
"local_uri": "127.0.0.1:'$((9000+i))'",
"log_file": "libp2p_node.log",
"public_uri": "127.0.0.1:'$((9000+i))'"
}'
aea config set vendor.fetchai.connections.prometheus.config.port $((20000+i))
aea config set vendor.fetchai.connections.http_server.config.port $((8000+i))
```

### Oracle integration (optional)

To publish the aggregated value to an oracle smart contract, add the ledger connection and simple oracle skill to one of the aggregators:
``` bash
aea add connection fetchai/ledger:0.19.0
aea add skill fetchai/simple_oracle:0.14.0
```

Configure the simple oracle skill for the `fetchai` ledger:
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id fetchai
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function update_oracle_value
```

Generate some wealth to use for transactions on the testnet ledger:
```
aea generate-wealth fetchai
```

Set the name of the oracle value to match the value collected by the aggregators:
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.oracle_value_name price_mean
```

### Run the AEAs

Run each of the aggregator AEAs in separate terminals: 
``` bash
aea run
```

After a few moments, you should see the AEAs finding peers, making observations, sending them to peers, and taking the average of their observations:
``` bash
info: [agg_i] found agents...
...
info: [agg_i] Fetching data from...
...
info: [agg_i] Observation: {'price': {'value':...
...
info: [agg_i] sending observation to peer...
...
info: [agg_i] received observation from sender...
...
info: [agg_i] Observations:...
...
info: [agg_i] Aggregation (mean):...
```
