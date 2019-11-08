## Get started

- Follow the instructions here to install the fetch.ai ledger:
    
      https://github.com/fetchai/ledger
  
  After you have the ledger setup you can run the following command to start the messenger server:
      
      ./libs/messenger/examples/example-messenger-messegner-server 
        

- Install the fetch-p2p-api to the aea framework:

      pip install git+https://github.com/fetchai/peer-to-peer-api.git


##Create the agent

- Create an aea agent:

      aea create my_agent

- Add the peer to peer connection:
     
      cd my_agent 
      aea add connection p2p


- Run the agent:

      aea run my_agent --connection p2p


In order to see that everything is running, you have to create an envelope and send it. 


