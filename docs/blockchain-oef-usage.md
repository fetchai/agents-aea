The AEA framework enables the agents to interact with the blockchain in the form of transaction completion. Currently, the framework supports
two different networks natively: the `Fetch.ai` network and the `Ethereum` network.

Consider the following use case:

Once the AEAs successfully end the negotiations, the buyer should send the correct amount to the specified wallet address. Then, the provider
validates the transaction digest and sends the data to the client.

The limitation of the previous use case is that we should trust the provider that he will send the data upon successful payment.

## Ledger Apis

We interact with the blockchains through a module called `LedgerApis`. The `ledger_apis` module contains implementations of each ledger API object (abstract class) that wraps the libraries of each network. With these implementations, we can create accounts for the specified networks. The account contains the private/public key pair and a wallet address. Also with the account, we will be able to
sign a transaction and send it to the network.  

## OEF

The 'Open Economic Framework' (OEF) is a node that enables us to search, discover and communicate with possible clients or services. For the AEAs to be able to find each other, one must register as a service and the other must query the OEF node for a service.  

## Communication

The following diagrams illustrates the interactions with the OEF and the blockchain for a scenario of a buyer-seller AEAs

<div class="mermaid">
    sequenceDiagram
        participant OEF
        participant Client_AEA
        participant Service_AEA
        participant Blockchain
    
        activate Client_AEA
        activate OEF
        activate Service_AEA
        activate Blockchain
        
        Service_AEA->>OEF: register_service
        Client_AEA->>OEF: search
        OEF-->>Client_AEA: list_of_agents
        Client_AEA->>Service_AEA: call_for_proposal
        Service_AEA->>Client_AEA: propose
        Client_AEA->>Service_AEA: accept
        Service_AEA->>Client_AEA: match_accept
        Client_AEA->>Blockchain: transfer_funds
        Client_AEA->>Service_AEA: send_transaction_hash
        Service_AEA->>Blockchain: check_transaction_status
        Service_AEA->>Client_AEA: send_data
        
        deactivate Client_AEA
        deactivate OEF
        deactivate Service_AEA
        deactivate Blockchain
       
</div>
