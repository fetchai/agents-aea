``` bash
agent_name="agg$i"
aea fetch fetchai/simple_aggregator:0.5.1 --alias $agent_name
cd $agent_name
aea install
aea build
```
``` bash
agent_name="agg$i"
aea create agent_name
cd agent_name
aea add connection fetchai/http_client:0.24.2
aea add connection fetchai/http_server:0.23.2
aea add connection fetchai/p2p_libp2p:0.27.1
aea add connection fetchai/soef:0.27.2
aea add connection fetchai/prometheus:0.9.2
aea add skill fetchai/advanced_data_request:0.7.2
aea add skill fetchai/simple_aggregation:0.3.2

aea config set agent.default_connection fetchai/p2p_libp2p:0.27.1
aea install
aea build
```
``` bash
aea config set --type int vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.decimals 0
```
``` bash
aea config set --type bool vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.use_http_server false
```
``` bash
aea config set --type list vendor.fetchai.connections.p2p_libp2p.cert_requests \
'[{"identifier": "acn", "ledger_id": "fetchai", "not_after": "2023-01-01", "not_before": "2022-01-01", "public_key": "fetchai", "message_format": "{public_key}", "save_path": ".certs/conn_cert.txt"}]'
```
``` bash
aea config set vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url $COIN_URL
aea config set vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs '[{"name": "price", "json_path": '"\"$JSON_PATH\""'}]'
```
``` bash
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.quantity_name price
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.aggregation_function mean
```
``` bash
SERVICE_ID=my_btc_aggregation_service
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.service_id $SERVICE_ID
aea config set vendor.fetchai.skills.simple_aggregation.models.strategy.args.search_query.search_value $SERVICE_ID
```
``` bash
aea generate-key fetchai
aea add-key fetchai
aea generate-key fetchai fetchai_connection_private_key.txt
aea add-key fetchai fetchai_connection_private_key.txt --connection
```
``` bash
aea issue-certificates
```
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
``` bash
aea add connection fetchai/ledger:0.21.1
aea add skill fetchai/simple_oracle:0.16.1
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.ledger_id fetchai
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.update_function update_oracle_value
```
```
aea generate-wealth fetchai
```
``` bash
aea config set vendor.fetchai.skills.simple_oracle.models.strategy.args.oracle_value_name price_mean
```
``` bash
aea run
```
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

