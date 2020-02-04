The AEA generic buyer and seller skills demonstrate an interaction between two AEAs.

* The provider of a service in the form of data for sale.
* The buyer of a service.

## Preparation instructions
 
### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

##Discussion

The scope of the specific demo is to demonstrate how to create an easy configurable AEA. The seller AEA
will sell the service specified in the `skill.yaml` file and deliver it upon payment by the buyer. Adding a database or hardware sensor for loading the data is out of the scope of this demo.
As a result, the AEA can provide data that are listed in the `skill.yaml` file.
This demo does not utilize a smart contract. We interact with a ledger only to complete a transaction.

Moreover, this example provides a way to customise the skill code and connect a database or sensor. 
You can modify the `has_data_source` variable in `skill.yaml` file of the generic_seller skill to True. Then you have to implement the method `collect_from_data_source(self)` inside the strategy.py file. 
### Launch an OEF node
In a separate terminal, launch a local OEF node (for search and discovery).
``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

Keep it running for all the following demos.

## Demo 1: Ledger payment

A demo to run a scenario with a true ledger transaction on Fetch.ai `testnet` or `Ethereum Ropsten testnet`. This demo assumes the buyer
trusts the seller AEA to send the data upon successful payment.

### Create the seller AEA (ledger version)

Create the AEA that will provide data.

``` bash
aea create my_seller_aea
cd my_seller_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/generic_seller:0.1.0
aea install
```

### Create the buyer client (ledger version)

In another terminal, create the AEA that will query the seller AEA.

``` bash
aea create my_buyer_aea
cd my_buyer_aea
aea add connection fetchai/oef:0.1.0
aea add skill fetchai/generic_buyer:0.1.0
aea install
```

Additionally, create the private key for the buyer AEA based on the network you want to transact.

To generate a key for Fetch.ai use:
```bash
aea generate-key fetchai
aea add-key fetchai fet_private_key.txt
```

To generate a key for Ethereum use:
```bash
aea generate-key ethereum
aea add-key ethereum eth_private_key.txt
```

### Update the AEA configs

Both in `my_seller_aea/aea-config.yaml` and
`my_buyer_aea/aea-config.yaml`, replace `ledger_apis: {}` with the following based on the network you want to connect

To connect to Fetchai:

``` yaml
ledger_apis:
  fetchai:
    network: testnet
```

To connect to Ethereum:
```yaml
ledger_apis:
  ethereum:
    address: https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe
    chain_id: 3
    gas_price: 50
```

### Update the seller AEA skill configs

In `my_seller_aea/vendor/fetchai/generi_seller/skill.yaml`, replace the `data_for_sale`, `datamodel`, and `scheme` with your data:
```bash
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|shared_classes:                    |shared_classes:                   |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      total_price: 10              |      total_price: 10             |
|      seller_tx_fee: 0             |      seller_tx_fee: 0            |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      has_data_source: False       |      has_data_source: False      |
|      data_for_sale:               |      data_for_sale:              |
|        wind: 10                   |        wind: 10                  |
|        pressure: 20               |        pressure: 20              |
|        temperature: 26            |        temperature: 26           |
|      datamodel:                   |      datamodel:                  |
|        Attribute1:                |        Attribute1:               |
|          name: country            |          name: country           |
|          type: str                |          type: str               |
|          is_required: True        |          is_required: True       |
|        Attribute2:                |        Attribute2:               |
|          name: city               |          name: city              |
|          type: str                |          type: str               |
|          is_required: True        |          is_required: True       |
|      scheme:                      |      scheme:                     |
|        country: UK                |        country: UK               |
|        city: Cambridge            |        city: Cambridge           |
|----------------------------------------------------------------------| 
```
The `datamodel` and the `scheme` are used to register the service in the OEF and make your agent discoverable. The name of each attribute must be a key in the `scheme` dictionary.

In the generic buyer skill config (`my_buyer_aea/skills/generic_buyer/skill.yaml`) under strategy change the `currency_id`,`ledger_id`, and at the bottom of the file the `ledgers`.

```bash
|----------------------------------------------------------------------|
|         FETCHAI                   |           ETHEREUM               |
|-----------------------------------|----------------------------------|
|shared_classes:                    |shared_classes:                   |              
|  strategy:                        |  strategy:                       |
|     class_name: Strategy          |     class_name: Strategy         |
|    args:                          |    args:                         |
|      max_price: 4                 |      max_price: 40               |
|      max_buyer_tx_fee: 1          |      max_buyer_tx_fee: 200000    |
|      currency_id: 'FET'           |      currency_id: 'ETH'          |
|      ledger_id: 'fetchai'         |      ledger_id: 'ethereum'       |
|      is_ledger_tx: True           |      is_ledger_tx: True          |
|      search_query:                |      search_query:               |
|        search_term: country       |        search_term: country      |
|        search_value: UK           |        search_value: UK          |
|        constraint_type: '=='      |        constraint_type: '=='     |
|ledgers: ['fetchai']               |ledgers: ['ethereum']             |
|----------------------------------------------------------------------| 
```

### Fund the buyer AEA

To create some wealth for your buyer AEA on the Fetch.ai `testnet`. (It takes a while).
``` bash
aea generate-wealth fetchai
```

To create some wealth for your thermometer client on the Ethereum Ropsten test net.

Go to the <a href="https://faucet.metamask.io/" target=_blank>MetaMask Faucet</a> and request some test ETH for the account your thermometer
client AEA is using (you need to first load your AEAs private key into MetaMask). Your private key is at `my_buyer_aea/eth_private_key.txt`.


## Run the AEAs

You can change the end point's address and port by modifying the connection's yaml file (my_thermometer_aea/connection/oef/connection.yaml)

Under config locate :

```bash
addr: ${OEF_ADDR: 127.0.0.1}
```
 and replace it with your ip (The ip of the machine that runs the oef image.)

Run both AEAs from their respective terminals

```bash 
aea add connection fetchai/oef:0.1.0
aea install
aea run --connections fetchai/oef:0.1.0
```
You will see that the AEAs negotiate and then transact using the Fetch.ai testnet.

## Delete the AEAs
When you're done, go up a level and delete the AEAs.
```bash 
cd ..
aea delete my_seller_aea
aea delete my_buyer_aea
```

## Communication
This diagram shows the communication between the various entities as data is successfully sold by the seller AEA to the buyer. 

<div class="mermaid">
    sequenceDiagram
        participant Search
        participant Buyer_AEA
        participant Seller_AEA
        participant Blockchain
    
        activate Buyer_AEA
        activate Search
        activate Seller_AEA
        activate Blockchain
        
        Seller_AEA->>Search: register_service
        Buyer_AEA->>Search: search
        Search-->>Client_AEA: list_of_agents
        Buyer_AEA->>Seller_AEA: call_for_proposal
        Seller_AEA->>Buyer_AEA: propose
        Buyer_AEA->>Seller_AEA: accept
        Seller_AEA->>Buyer_AEA: match_accept
        Buyer_AEA->>Blockchain: transfer_funds
        Buyer_AEA->>Seller_AEA: send_transaction_hash
        Seller_AEA->>Blockchain: check_transaction_status
        Seller_AEA->>Buyer_AEA: send_data
        
        deactivate Buyer_AEA
        deactivate Search
        deactivate Seller_AEA
        deactivate Blockchain
       
</div>
