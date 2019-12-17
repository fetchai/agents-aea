# Agent-oriented problem solving
In this section, we highlight some of the most fundamental characteristics of the agent-based approach to solution development, and problem solving in general, which may be different from some of the existing paradigms and methodologies people are used to. We hope to be able to guide you towards having the right mindset when designing your own agent-based solutions to real world problems. 

<!-- Our aim with the following discussion is that we guide you--> 

## Decentralisation
First and foremost is decentralisation. Multi-agent systems (MAS) are inherently decentralised. The vision is an environment in which every individual is able to directly connect with everyone else and interact with them without having to rely on a third-party to facilitate this. This is in direct contrast to centralised systems in which a single entity is the central point of authority, through which all interactions happen. Systems based on the client-server model are an example of centralised systems in which <!--a central facility (the server) provides a set of services to the clients. Furthermore, in these systems,--> clients interact with one another, regarding a specific service (e.g. communication, trade), through the server. 

Note, this is not to say that facilitators and middlemen have no place in a Multi-Agent System; rather it is the 'commanding reliance on middlemen' that MAS disagrees with.

In a decentralised system, every agent is equally privileged, and in principle, is able to interact with other agents. The idea is very much aligned with the peer-to-peer paradigm in which the voluntary participation and contribution of peers creates an infrastructure. As such, in a decentralised system, there is no central 'enforcer'. This means all the work that would typically fall under the responsibilities of a central entity must be performed by individual parties in a decentralised system. Blockchain-based cryptocurrencies are a good example of this. People who are getting into cryptocurrencies are often reminded that, due to the lack of a central trusted entity (e.g. a bank), most security precautions related to the handling of digital assets and the execution of transactions fall on individuals themselves. 

Another example is the verification of protocol adherence in regulated systems. Consider the problem of traffic management. The success of such a system relies on its participants (e.g. pedestrians, cars, motorbikes, bicycles, etc) conforming with the traffic management protocol, which specifies, for instance, who has the right of way in a junction. It is trivial that for the continuous functioning of this system, the existence of a protocol is not enough. There should also be a mechanism in place that verifies the participants follow the protocol. In a central system, verifying whether parties adhere to the system's protocol is often the responsibility of a central unit that checks (some or all) actions of the parties involved. The police could be considered a central entity that enforces traffic protocols and punishes those violating it. However, in a decentralised environment, this burden falls on the parties involved in the interaction themselves. Therefore, one could imagine a self-governing structure whereby individuals on the road enforce protocol adherence on each other and decide on the appropriate method(s) of enforcement (e.g. through collective punishments, sanctions, rewards, ratings, etc).

It is important to emphasise that by decentralisation we do not mean distribution; although multi-agent systems typically do tend to be distributed. A distributed system is one whose components are physically located in different places and connected over a network. A fully centralised system, owned and operated by a single entity, may in fact be highly distributed. Google's infrastructure is an example of this, where all of the components are distributed across the globe, yet designed to work together highly efficiently, and function in unison. Decentralisation on the other hand refers to a system whose components may be owned, operated, and managed by different stakeholders, each with their own personal objectives, interests, and preferences, which may not necessarily be aligned with one another or that of the system itself. Therefore, distribution refers to the physical placement of a system's components, whereas decentralisation refers to a) the diversity of ownership and control over a system's constituents, and b) the absence of a central point of authority between them.    

To better illustrate the distinction between centralised and decentralised systems, consider search and discoverability in a commerce environment. In a central system (say amazon.com), there is a single search service provider -- owned and run by the commerce company itself -- which takes care of all search related functionality for every product within their domain. So to be discoverable in this system, all sellers must register their products with this particular search service provider. However in a decentralised system, there may not necessarily be a single search service provider. There may be multiple such providers, run by different, perhaps competing entities. Each seller has the freedom to register with (i.e. make themselves known to) one or a handful of providers. On the buyers side, the more providers they contact and query, the higher their chances of finding the product they are looking for. 

## Conflicting Environment

Another characteristic of multi-agent systems, which is a direct consequence of their decentralisation, is their conflicting nature. As discussed above, the notion of decentralisation extends as far as ownership and control. Therefore, the different components that make up a decentralised system may each be owned by a different entity, designed according to very different principles and standards, with heterogeneous software and hardware, and each with internal objectives that may be fundamentally inconsistent, worst yet contradictory, with those of others. 

<!--As their name suggest, there are more than one agent in a multi-agent environment, each changing the state of the environment to their own liking. Crucially, as a decentralised system, MAS makes no such assumption that agents are owned by the same entity, or designed homogeneously along the same line of standards and principles. In fact, a distinctive characteristic of a multi-agent environment is that it is inhabited by more than one agent, each being owned by a different stakeholder (individual, company, government).-->

As such, a distinctive characteristic of a multi-agent environment is that it is inhabited by more than one agent, as the name suggests :), where each agent may be owned potentially by a different stakeholder (individual, company, government). Since by design each agent represents and looks after the interests of its owner(s), and because different stakeholders may have unaligned, conflicting, or contradictory interests, it is very common that in a multi-agent system, the agents' objectives, values and preferences may also be unaligned, conflicting, or contradictory.

There are practical implications that follow from the above when it comes to designing an agent. For example, it is not rational for an agent to automatically rely on the information it receives from other agents. The information could be incomplete; what is unrevealed may have been deemed private for strategic reasons. The information could be uncertain, the result of an inaccurate prediction. Or it could be an outright lie, due to the adversarial nature of the environment. Therefore there is a degree of uncertainty attached to almost all information an agent receives in a multi-agent system. One could argue for taking a sceptical approach; treating everything as uncertain, unless proved otherwise.  

Therefore when designing an agent, one has to be aware of this conflicts of interest, and take this into account when for example the agent gathers information from other agents .    

## Asynchronization

Another inherent difference: Agents are autonomous, thus:

**Asynchronization**; agent vs object (want vs must); no guarantees w.r.t. Responses (may lie/incomplete (see above), respond later (you are low priority to them), don’t respond because they don’t want to)

In practice: your decision making and action should be as much as possible independent of interactions with others; decoupling of decision/actions and interactions. Try to interact with others but decide/act based on information/responses you have and shouldn’t wait to get all responses

## Complex, Incomplete, Inconsistent and Uncertain

Be aware that usually:

**Complex** world, (thus, since hard to see everything) **incomplete** information/model of the world, (even worse) **inconsistent** information, (thus, due to the last two) **uncertain** knowledge. 

In practice: there are degrees of uncertainty to information (partly due to conflict), e.g. information received may not be fully trusted, based on (not fully accurate) predictions.

Cannot write a programme in which you make calls to sources, wait for all to come back and act based on the collection of all responses. The other agents may not come back to you (selfish, autonomy), may come back later on (autonomy, agent vs object) when the response is no longer useful for you, their information may be incomplete/incorrect (conflicting interest), may be uncertain (based on flawed prediction), inconsistent with information from other sources. So should build an approximate model based on all the information one has. 

<br />
