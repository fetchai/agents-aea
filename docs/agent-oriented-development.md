# Agent-oriented development

This section introduces concepts and characteristics of agent-based systems and 
problem-solving approaches. At the end of this section the reader will know how 
problems can be contextualized in a way that allows them to be addressed by 
agent-based systems, and possess the necessary knowledge to start working on 
the design and implementation of agent-based solutions to real world problems.


## Decentralisation

Allowing for direct peer-to-peer communication makes Multi-Agent Systems 
(**MAS**) inherently decentralized. This contrasts conventional systems design, 
such as that of the client-server model, in which clients are forced to trust 
the server host - a central point of authority in the network - as the mediator 
of all client interactions. That does not imply that facilitators of services 
and middlemen have no place in a multi-agent system; rather it is the notion of 
a '_commanding reliance on middlemen_' that is rejected.

Lack of a centralized authority is not their only distinctive characteristic. 
The agents and their components - those enabling them to enact, react and engage
in decision-making - generally belong to different stakeholders - e.g. 
individuals, companies or governments - and need to share no more commonality 
than a network connection and an interaction protocol to be able to interact. 
The consequence hereof is that they can be exceptionally diverse in terms of
their design, the standards they adhere to, the software used to implement them 
and the hardware they operate on. Moreover, each of the agents has their own 
objectives, which may well be unaligned, inconsistent or even conflicting with 
those of others.

**Division of responsibilities:** In a decentralised system every agent is 
equally privileged and (in principle) able to interact with any other agent. 
Without a central authority that provides the services needed to mediate agent 
interactions, hosting them becomes part of the agents' responsibility. An 
example hereof is the access to a registry of contact addresses that is 
otherwise maintained by a service provider. Without any form of government, 
however, a central database that can be updated at the sole discretion of any 
individual agent is easily corrupted. Yet, a system in which every agent is only
responsible for maintaining their own set of records is also problematic, since 
errors and the asynchronous execution of events inevitably leads to a situation 
in which agents possess different versions of the record. Instead, agents must 
share responsibility over the state of records and do so by maintaining a local 
copy of it and periodically synchronizing this state by requiring consensus to 
be achieved over it and any updates to it. 

Distributed ledger technologies, such as blockchain-based cryptocurrencies, are
a prime example of this. A characteristic feature of cryptocurrencies is the 
absence of central trusted entities (e.g. banks). The notion of decentralisation
extends as far as ownership and control. Although enabled through the use of 
open source code and cryptographic primitives offering security precautions, 
the validation of transactions and accuracy of ledger is ultimately the 
responsibility of individuals.

<!--Another example is the verification of protocol adherence in regulated systems. Consider the problem of traffic management. The success of such a system relies on its participants (e.g. pedestrians, cars, motorbikes, bicycles, etc.) conforming with the traffic management protocol, which specifies, for instance, who has the right of way in a junction. It is trivial, that the continuous functioning of this system does not rest solely on the existence of a protocol; there should also be a mechanism in place that verifies the protocol is followed by the participants. In a central system, verifying whether parties adhere to the system's protocol is often the responsibility of a central unit that checks (some or all) actions of the parties involved. The police could be considered a central entity that enforces traffic protocols and punishes those violating it. However, in a decentralised environment, this burden falls on the parties involved in the interaction themselves. Therefore, one could imagine a self-governing traffic management system whereby individuals on the road enforce protocol adherence on each other and decide on the appropriate method(s) of enforcement (e.g. through collective punishments, sanctions, rewards, ratings, etc).-->

**Decentralised vs distributed:** 
It is important to distinguish the concepts of distributed and decentralised 
systems. A distributed system is one whose components are physically separated 
and connected over a network, whereas a decentralised system requires control 
over its governance to be shared among its stakeholders. Google or Microsoft's 
cloud infrastructure are examples of the former; nodes of these networks are 
distributed across the globe, yet these systems are centralized because 
governance over them resides solely with centralized entities.

**Example:** 
To better illustrate the distinction between centralised and decentralised 
systems, consider another example: search and discoverability in a commerce 
environment. In a centralised system (say Amazon), there is a single search 
service - provided, owned and run by the commerce company itself - which takes 
care of all search-related functionality for every product within their domain.
So to be discoverable in this system, all sellers must register their products 
with this particular service. However, in a decentralised system, there may not
necessarily be a single search service provider. There may be multiple such 
services, run by different, perhaps competing entities. Each seller has the 
freedom to register with (i.e. make themselves known to) one or a handful of 
services. On the buyers side, the more services they contact and query, the 
higher their chances of finding the product they are looking for.


## Conflicting Environment

Since decentralisation implies shared ownership and control of governance, with 
each of the entities in these networks acting in pursuit of their own objectives,
conflicts of interest are expected to arise. Practical implications hereof on 
the design of agents that need to be considered by a developer are that 
information available to it is:

* Incomplete: what is unrevealed may have been deemed private for strategic reasons. 
* Uncertain: it may be the result of an inaccurate prediction. 
* Incorrect: it could be an outright lie, due to the adversarial nature of the environment.

This uncertainty poses a challenge to the agents, who, since they cannot blindly trust other agents, need to validate the information that they provide.


## Asynchronous task execution


A system of self-interested agents favours a design that allowed for asynchronous execution, such that agents can express behaviour independently each other.

**Asynchronous programming:** Generally speaking, asynchronous programming allows the decoupling of the tasks that the agents carry out via concurrent processing. This leads to uncertainty regarding the behaviour of the system, since the order of code execution will vary. For example, suppose an agent `i` sends a message requesting some resources from an agent `j`. Since agents are distributed, there is uncertainties associated with the communication over a network: `j` may never receive `i`'s request, or may receive it after a long delay. Furthermore, `j` could receive the request in time and respond immediately, but as mentioned in the last section, its answer might be incomplete (gives only some of the requested resources), uncertain (promises to give the resources, but cannot be fully trusted), or incorrect (sends a wrong resource). In addition, since agents are self-interested, `j` may _decide_ to reply much later, to the point that the resource is no longer useful to agent `i`, or `j` may simply decide not to respond at all. There is a myriad of reasons why it may choose to do that. The take away is that agents' autonomy strongly influences what can be expected of them, and of an environment inhabited by them. This makes developing applications for systems whose constituents are autonomous fundamentally different from conventional object-oriented systems design.

**Objects vs agents:** In object-oriented systems, objects are entities that encapsulate state and perform actions, i.e. call methods, on this state. In object-oriented languages, like C++ and Java, it is common practice to declare methods as public, so they can be invoked by other objects in the system whenever they wish. This implies that an object has no control over access to its attributes or the execution of its methods by other objects in the system.  

We cannot take for granted that an agent `i` will execute an action (the equivalent of a method in object-oriented systems) just because another agent `j` wants it to. We therefore do not think of agents as invoking methods on one another, rather as _requesting_ actions. If `i` requests `j` to perform an action, then `j` may or may not perform the action. The control structure of these systems in different and can be summarised with the following slogan (from <a href="https://www.wiley.com/en-gb/An+Introduction+to+MultiAgent+Systems%2C+2nd+Edition-p-978EUDTE00553" target="_blank">An Introduction to MultiAgent Systems</a> by <a href="https://www.cs.ox.ac.uk/people/michael.wooldridge/" target="_blank">Michael Wooldridge</a>):
>objects do it for free; agents do it because they want to.


## Time

Closely related with the discussion of asynchronicity, is the idea that in multi-agent systems, time is not a universally agreed notion. Agents may not necessarily share the same clock and this fact must be taken into account when designing agent-based systems. For example, you cannot necessarily expect agents to synchronise their behaviour according to time (e.g. perform a certain task at a time `X`). 

Another related issue, is that unlike some agent-based simulation (ABS) systems where there is a global tick rate for all agents, in AEA-based systems tick rates may be different for different agents. This is due to the fundamental difference that ABS systems control some aspects of all of their agents' executions while in AEA-based systems, agents are truly decoupled from one another  - most likely distributed and running on different machines and networks - and there is absolutely no central unit that moderates any aspect of their behaviour.    

## Complex, Incomplete, Inconsistent and Uncertain

The fourth characteristic(s) relate to the environment in which agents are expected to operate in, and these have been mentioned a number of times in the previous sections.

The environment agents are suited for typically tend to be complex, to the point that it is usually impossible for any single agent to perceive the whole of the environment on its own. This means that at any point in time, any agent has a limited knowledge about the state of the environment. In other words, the agents;' information tend to be incomplete due to the complexity and sophistication of the world in which they reside. 

Consider an agent which represents a driverless vehicle. The complexity of the problem of driving on the road makes it impossible for a single vehicle to have an accurate and up-to-date knowledge of the overall state of the world . This means that an agent's model of the world is at best uncertain. For instance, the vehicle, through its sensor may detect green light at a junction, and by being aware of what it means, it may infer that it is safe to cross a junction. However, that simply may not be true as another car in the opposite direction may still cross the junction violating their red light. Therefore, there is uncertainty associated with the knowledge "it is safe to cross the road because the light is green", and the agent must recognise that. 

Furthermore, the often conflicting nature of the environment means information obtained from multiple sources (agents) may be inconsistent. Again, this must be taken into consideration when designing an agent which is expected to operate successfully in a potentially conflicting environment. 

## Further Reading

* Wooldridge, M. (2009). _An Introduction to MultiAgent Systems_. Wiley, Second edition.
* Shoham, Y. and Leyton-Brown, K. (2008). _Multiagent Systems: Algorithmic, Game-Theoretic, and Logical Foundations_. Cambridge University Press

<br />
