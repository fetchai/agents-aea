The AEA framework uses the 'Open Economic Framework' (OEF) to be able to search and discover agents but this doesn't 
mean that we cannot use any other framework if we implement the connection wrapper.

## How the AEAs talk to each other

Each AEA has an inbox and an outbox queue that is used to receive or send messages. These queues receive/send `envelopes`.
As we said in  <a href='/core-components/'>  core components </a>, each envelope must specify the protocol that is
implemented in the message. So for two AEAs to be able to communicate the need to support the same protocol and to exist in the same environment. 

The AEA framework works natively with the OEF to enable us to search and discover other AEAs. For better understanding consider the 
following scenario:

AEA_1 sends a message to the OEF and registers itself as a service in the UK.
 
AEA_2 sends a message to the OEF and asks for services based on the location and specifically in the UK. 

Then the OEF will search and find all the AEAs that match the query of AEA_2 and will return these AEAs as a list (AEA_1 will be in this list).
The list contains the name and the address of each AEA. Finally, the AEA_2 can create a new envelope that will specify the address of the AEA_1
in the field `to` and will send it through the OEF.
