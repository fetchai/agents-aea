<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This demo is incomplete and will soon be updated.
</p>
</div>

Demonstrating an entire decentralised identity scenario involving AEAs and instances of Aries Cloud Agents (ACAs).

## Discussion

This demo corresponds with the one <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/main/demo/README.md" target="_blank">here</a> from <a href="https://github.com/hyperledger/aries-cloudagent-python" target="_blank"> Aries cloud agent repository </a>.

The aim of this demo is to illustrate how AEAs can connect to ACAs, thus gaining all of their capabilities, such as issuing and requesting verifiable credentials, selective disclosure and zero knowledge proofs.

<div class="mermaid">
    sequenceDiagram
        participant faea as Faber_AEA
        participant faca as Faber_ACA
        participant aaca as Alice_ACA
        participant aaea as Alice_AEA

        activate faea
        activate faca
        activate aaca
        activate aaea

        Note right of aaea: Shows P2P ID

        faea->>faca: Request status?
        faca->>faea: status
        faea->>faca: Register schema
        faca->>faea: schema_id
        faea->>faca: Register credential definition
        faca->>faea: credential_definition_id
        faea->>faca: create-invitation
        faca->>faea: connection inc. invitation
        faea->>aaea: invitation detail
        aaea->>aaca: receive-invitation

        deactivate faea
        deactivate faca
        deactivate aaca
        deactivate aaea
</div>

There are two AEAs:

 * **Alice_AEA**
 * **Faber_AEA**

and two ACAs:

 * **Alice_ACA**
 * **Faber_ACA**

Each AEA is connected to its corresponding ACA: **Alice_AEA** to **Alice_ACA** and **Faber_AEA** to **Faber_ACA**.

The following lists the sequence of interactions between the four agents:

 * **Alice_AEA**: starts
 * **Alice_AEA**: shows its P2P address in the terminal and waits for an `invitation` detail from **Faber_AEA**.
 * **Alice_AEA**: registers itself on the SOEF.
 * **Faber_AEA**: starts
 * **Faber_AEA**: searches the SOEF and finds **Alice_AEA**.
 * **Faber_AEA**: tests its connection to **Faber_ACA**.
 * **Faber_ACA**: responds to **Faber_AEA**.
 * **Faber_AEA**: registers a DID on the ledger.
 * **Faber_AEA**: request **Faber_ACA** to register a schema on the ledger.
 * **Faber_ACA**: responds by sending back the `schema_id`.
 * **Faber_AEA**: request **Faber_ACA** to register a credential definition on the ledger.
 * **Faber_ACA**: responds by sending back the `credential_definition_id`.
 * **Faber_AEA**: requests **Faber_ACA** to create an invitation.
 * **Faber_ACA**: responds by sending back the `connection` detail, which contains an `invitation` field.
 * **Faber_AEA**: sends the `invitation` detail to **Alice_AEA**.
 * **Alice_AEA**: receives `invitation` detail from **Faber_AEA**.
 * **Alice_AEA**: requests **Alice_ACA** to accept the invitation, by passing it the `invitation` detail it received in the last step.

All messages from an AEA to an ACA are http requests (using `http_client` connection).

All messages from an AEA to another AEA utilise the P2P communication network accessed via the `p2p_libp2p` connection.

All messages initiated from an ACA to an AEA are webhooks (using `webhook` connection).

This is the extent of the demo at this point. The rest of the interactions require an instance of the <a href="https://github.com/bcgov/von-network" target="_blank">Indy ledger</a> to run. This is what will be implemented next.

The rest of the interactions are broadly as follows:

 * **Alice_ACA**: accepts the invitation.
 * **Alice_ACA**: sends a matching invitation request to **Faber_ACA**.
 * **Faber_ACA**: accepts

At this point, the two ACAs are connected to each other.

 * **Faber_AEA**: requests **Faber_ACA** to issue a credential (e.g. university degree) to **Alice_AEA**, which **Faber_ACA** does via **Alice_ACA**.
 * **Faber_AEA**: requests proof that **Alice_AEA**'s age is above 18.
 * **Alice_AEA**: presents proof that it's age is above 18, without presenting its credential.

## Preparation Instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start. 

Install Aries cloud-agents (for more info see <a href="https://github.com/hyperledger/aries-cloudagent-python#install" target="_blank">here</a>) if you do not have it on your machine:

``` bash
pip install aries-cloudagent
```

This demo has been successfully tested with `aca-py` version `0.4.5`.

This demo requires an instance of von network running in docker locally (for more info see <a href="https://github.com/bcgov/von-network#running-the-network-locally" target="_blank">here</a>)

This demo has been successfully tested with the von-network git repository pulled on 07 Aug 2020 (commit number `ad1f84f64d4f4c106a81462f5fbff496c5fbf10e`). 

### Terminals

Open five terminals. The first terminal is used to run an instance of von-network locally in docker. The other four terminals will be used to run each of the four agents in this demo.

## VON Network

In the first terminal move to the `von-network` directory and run an instance of `von-network` locally in docker.

This <a href="https://github.com/bcgov/von-network#running-the-network-locally" target="_blank">tutorial</a> has information on starting (and stopping) the network locally.

``` bash
./manage build
./manage start --logs
``` 
Once the ledger is running, you can see the ledger by going to the web server running on port 9000. On localhost, that means going to <a href="http://localhost:9000" target="_blank">http://localhost:9000</a>.  

## Alice and Faber ACAs

To learn about the command for starting an ACA and its various options:

``` bash
aca-py start --help
```

### Faber_ACA

In the first terminal:

``` bash
aca-py start --admin 127.0.0.1 8021 --admin-insecure-mode --inbound-transport http 0.0.0.0 8020 --outbound-transport http --webhook-url http://127.0.0.1:8022/webhooks
```

Make sure the ports above are unused.

Take note of the specific IP addresses and ports you used in the above command. We will refer to them by the following names:

* **Faber admin IP**: 127.0.0.1
* **Faber admin port**: 8021
* **Faber webhook port**: 8022

The admin IP and port will be used to send administrative commands to this ACA from an AEA.

The webhook port is where the ACA will send notifications to. We will expose this from the AEA so it receives this ACA's notifications.

### Alice_ACA

In the second terminal:

``` bash
aca-py start --admin 127.0.0.1 8031 --admin-insecure-mode --inbound-transport http 0.0.0.0 8030 --outbound-transp http --webhook-url http://127.0.0.1:8032/webhooks
```

Again, make sure the above ports are unused and take note of the specific IP addresses and ports. In this case:

* **Alice admin IP**: 127.0.0.1
* **Alice admin port**: 8031
* **Alice webhook port**: 8032

## Alice and Faber AEAs

Now you can create **Alice_AEA** and **Faber_AEA** in terminals 3 and 4 respectively.

### Alice_AEA

In the third terminal, fetch **Alice_AEA** and move into its project folder:

``` bash
aea fetch fetchai/aries_alice:0.31.0
cd aries_alice
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create <b>Alice_AEA</b> from scratch:
``` bash
aea create aries_alice
cd aries_alice
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/http_client:0.23.0
aea add connection fetchai/webhook:0.19.0
aea add skill fetchai/aries_alice:0.24.0
```
</p>
</details>

#### Configure the `aries_alice` skill:

(configuration file: `alice/vendor/fetchai/skills/aries_alice/skill.yaml`) 

Ensure `admin_host` and `admin_port` values match with the values you noted above for **Alice_ACA**. You can use the framework's handy `config` <a href="../cli-commands">CLI command</a> to set these values:

``` bash
aea config set vendor.fetchai.skills.aries_alice.models.strategy.args.admin_host 127.0.0.1
```
``` bash
aea config set --type int vendor.fetchai.skills.aries_alice.models.strategy.args.admin_port 8031
```

#### Configure the `webhook` connection:

(configuration file: `alice/vendor/fetchai/connections/webhook/connection.yaml`).

First ensure the value of `webhook_port` matches with what you used above for **Alice_ACA**.

``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8032
```

Next, make sure the value of `webhook_url_path` is `/webhooks/topic/{topic}/`.

``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```

#### Configure the `p2p_libp2p` connection:

``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11000",
  "entry_peers": [],
  "local_uri": "127.0.0.1:7000",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:7000"
}'
```

### Install the Dependencies and Run Alice_AEA:

Now install all the dependencies:

``` bash
aea install
aea build
```

Finally run **Alice_AEA**:

``` bash
aea run
```

Once you see a message of the form `To join its network use multiaddr 'SOME_ADDRESS'` take note of the address. (Alternatively, use `aea get-multiaddress fetchai -c -i fetchai/p2p_libp2p:0.25.0 -u public_uri` to retrieve the address.) We will refer to this as **Alice_AEA's P2P address**.

### Faber_AEA

In the fourth terminal, fetch **Faber_AEA** and move into its project folder:

``` bash
aea fetch fetchai/aries_faber:0.31.0
cd aries_faber
```

<details><summary>Alternatively, create from scratch.</summary>
<p>

The following steps create <b>Faber_AEA</b> from scratch:
``` bash
aea create aries_faber
cd aries_faber
aea add connection fetchai/p2p_libp2p:0.25.0
aea add connection fetchai/soef:0.26.0
aea add connection fetchai/http_client:0.23.0
aea add connection fetchai/webhook:0.19.0
aea add skill fetchai/aries_faber:0.22.0
```
</p>
</details>

#### Configure the `aries_faber` skill:

(configuration file: `faber/vendor/fetchai/skills/aries_alice/skill.yaml`)

Ensure `admin_host` and `admin_port` values match with those you noted above for **Faber_ACA**.

``` bash
aea config set vendor.fetchai.skills.aries_faber.models.strategy.args.admin_host 127.0.0.1
```

``` bash
aea config set --type int vendor.fetchai.skills.aries_faber.models.strategy.args.admin_port 8021
```

#### Configure the `webhook` connection:

(configuration file: `faber/vendor/fetchai/connections/webhook/connection.yaml`).

First, ensure the value of `webhook_port` matches with what you used above for **Faber_ACA**.

``` bash
aea config set --type int vendor.fetchai.connections.webhook.config.webhook_port 8022
```

Next, make sure the value of `webhook_url_path` is `/webhooks/topic/{topic}/`.

``` bash
aea config set vendor.fetchai.connections.webhook.config.webhook_url_path /webhooks/topic/{topic}/
```

#### Configure the `p2p_libp2p` connection:

``` bash
aea config set --type dict vendor.fetchai.connections.p2p_libp2p.config \
'{
  "delegate_uri": "127.0.0.1:11001",
  "entry_peers": ["SOME_ADDRESS"],
  "local_uri": "127.0.0.1:7001",
  "log_file": "libp2p_node.log",
  "public_uri": "127.0.0.1:7001"
}'
```

where `SOME_ADDRESS` is **Alice_AEA's P2P address** as displayed in the third terminal.

### Install the Dependencies and Run Faber_AEA:

Now install all the dependencies:

``` bash
aea install
aea build
```

Finally run **Faber_AEA**:

``` bash
aea run
```

You should see **Faber_AEA** running and showing logs of its activities. For example:

<img src="../assets/aries-demo-faber.png" alt="Aries demo: Faber terminal" class="center">

Looking now at **Alice_AEA** terminal, you should also see more activity by **Alice_AEA** after **Faber_AEA** was started. For example:

<img src="../assets/aries-demo-alice.png" alt="Aries demo: Alice terminal" class="center">

The last error line in **Alice_AEA**'s terminal is caused due to the absence of an Indy ledger instance. In the next update to this demo, this will be resolved.

## Terminate and Delete the Agents

You can terminate each agent by pressing Ctrl+C.

To delete the AEAs, go to the projects' parent directory and delete the AEAs:

``` bash
aea delete aries_faber
aea delete aries_alice
```

## Further developments

In the next update to this demo, the remaining interactions between AEAs and ACAs must be implemented. This means:

* An instance of Indy ledger must be installed and running. See <a href="https://github.com/bcgov/von-network#running-the-network-locally" target="_blank">here</a> for more detail.
* The commands for running the ACAs need to be adjusted. Additional options relating to a wallet (wallet-name, type, key, storage-type, configuration, credentials) need to be fed to the ACAs as well as the ledger's genesis file so the ACAs can connect to the ledger.
* The remaining interactions between the AEAs and ACAs as described <a href="../aries-cloud-agent-demo/#discussion">here</a> need to be implemented.