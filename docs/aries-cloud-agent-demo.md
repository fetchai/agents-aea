<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This demo is incomplete and will soon be updated.
</p>
</div>

Demonstrating an entire decentralised identity scenario involving AEAs and instances of Aries Cloud Agents (ACAs).

## Discussion

This demo corresponds with the one <a href="https://github.com/hyperledger/aries-cloudagent-python/blob/master/demo/README.md" target=_blank>here</a> from <a href="https://github.com/hyperledger/aries-cloudagent-python" target=_blank> aries cloud agent repository </a>. 

There are two AEAs: 

 * Alice_AEA
 * Faber_AEA 

and two ACAs:

 * Alice_ACA
 * Faber_ACA
 
Each AEA is connected to its corresponding ACA: Alice_AEA to Alice_ACA and Faber_AEA to Faber_ACA.

The following lists the sequence of interactions between the four agents:

 * Alice_AEA: starts
 * Alice_AEA: shows its identity in the terminal and waits for an `invitation` detail from Faber_AEA.
 * Faber_AEA: starts
 * Faber_AEA: tests its connection to Faber_ACA.
 * Faber_ACA: responds to Faber_AEA.
 * Faber_AEA: requests Faber_ACA to create an invitation.
 * Faber_ACA: responds by sending back the `connection` detail, which contains an `invitation` field.
 * Faber_AEA: sends the `invitation` detail to Alice_AEA.
 * Alice_AEA: receives `invitation` detail from Faber_AEA.
 * Alice_AEA: requests Alice_ACA to accept the invitation, by passing it the `invitation` detail it received in the last step.

All messages from an AEA to an ACA are http requests (using `http_client` connection).

All messages from an AEA to another AEA are via the `oef` connection.

All messages initiated from an ACA to an AEA are webhooks (using `webhook` connection).

This is the extent of the demo, at this point. The rest of the interactions require an instance of the <a href="https://github.com/bcgov/von-network" target=_blank>Indy ledger</a> to run. This is what will be implemented next.

The rest of the interactions are broadly as follows:

 * Alice_ACA: accepts the invitation.
 * Alice_AEA: sends a matching invitation request to Faber_ACA.
 * Faber_ACA: accepts

At this point Alice_ACA and Faber_ACA are connected. 

 * Faber_AEA: issues a credential (e.g. university degree) to Alice_AEA, via Faber_ACA and Alice_ACA.
 * Faber_AEA: requests proof that Alice_AEA's age is above 18.
 * Alice_AEA: presents proof that it's age is above 18, without presenting its credential.       
 
The aim of this demo is to illustrate how AEAs can connect to ACAs, thus gaining all of their capabilities, such as issuing and requesting verifiable credential, selective disclosure and zero knowledge proof.

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

## ACA

### Install ACA

Install Aries cloud-agents (run `pip install aries-cloudagent` or see <a href="https://github.com/hyperledger/aries-cloudagent-python#install" target=_blank>here</a>) if you do not have it on your machine.

## Run the ACAs

Open four terminals. Each terminal will be used to run one of the four agents in this demo. 

### Run Faber_ACA: 

Type this in the first terminal:

``` bash
aca-py start --admin 127.0.0.1 8021 --admin-insecure-mode --inbound-transport http 0.0.0.0 8020 --outbound-transport http --webhook-url http://127.0.0.1:8022/webhooks
```

Make sure the above ports are unused. To learn more about the above command for starting an aca and its various options: 

``` bash
aca-py start --help
```

### Run Alice_ACA: 

Type this in the second terminal:

``` bash
aca-py start --admin 127.0.0.1 8031 --admin-insecure-mode --inbound-transport http 0.0.0.0 8030 --outbound-transp http --webhook-url http://127.0.0.1:8032/webhooks
```

Again, make sure the above ports are unused.

## Run the AEAs

### Run Alice_AEA: 

In the third terminal, make sure you are in the Alice_AEA project folder. Then:

``` bash
aea run --connections fetchai/http_client:0.1.0,fetchai/oef:0.1.0,fetchai/webhook:0.1.0
```

You should see Alice_AEA running and showing its identity, something like:

``` bash
My address is: FRxXBaKvt9XwzdiQnMS8f6rXfUzi6ZCDb2UR1x4sr7WMo2SpH
```

### Run Faber_AEA: 

In the forth terminal, ensure you are in the Faber_AEA project folder. Then:

``` bash
aea run --connections fetchai/http_client:0.1.0,fetchai/oef:0.1.0,fetchai/webhook:0.1.0
```

You should see Faber_AEA running and showing logs of its activities. For example: 

<center>![Aries demo: Faber terminal](assets/aries-demo-faber.png)</center>

Looking now at the Alice_AEA terminal, you should also see more activity by Alice_AEA, after Faber_AEA was started. For example:

<center>![Aries demo: Alice terminal](assets/aries-demo-alice.png)</center>

The last error line in Alice_AEA terminal is caused due to the absence of an Indy ledger instance. In the next update to this demo, this will be resolved. 