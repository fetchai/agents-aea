

The AEA framework provides the tools for creating Autonomous Economic Agents (AEA).

## What are AEAs?

We define an autonomous economic agent or AEA as:

> An intelligent agent acting on an owner's behalf, with limited or no interference, and whose goal is to generate economic value for its owner.

<iframe width="560" height="315" src="https://www.youtube.com/embed/xpJA4IT5X88" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

An AEA represents an individual, organisation or object and looks after its interests. AEAs act independently of constant input from their owner and autonomously execute actions to achieve their prescribed goals. Their purpose is to create economic value for you, their owner, in clearly defined domains. AEAs have a wide range of <a href="app-areas">application areas</a> and we provide <a href="demos">demo guides</a> to highlight examples of their use cases.

### What is not an AEA

* Any <a href="https://en.wikipedia.org/wiki/Software_agent" target="_blank">agent</a>: AEAs' purpose is to generate economic value in a multi-stakeholder environment with competing incentives between agents. They represent humans, organisations or objects.
* APIs or sensors which do not have agency.
* <a href="https://en.wikipedia.org/wiki/Smart_contract" target="_blank">Smart contracts</a> which do not display any proactiveness and are purely reactive to external requests (=contract calls and transactions). 
* <a href="https://en.wikipedia.org/wiki/Artificial_general_intelligence" target="_blank">Artificial General Intelligence (AGI)</a>. AEAs can have a very narrow, goal directed focus involving some economic gain and can have a very simple logic.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>In the rest of the documentation, unless specified otherwise, we use the terms AEA and agent interchangeably to refer to AEA as defined above.</p>
</div>

## What is the AEA Framework?

The AEA framework is a development suite, currently implemented in Python, which equips you with an efficient and accessible set of tools for building and running AEAs. The framework is modular, extensible, and composable. It attempts to make agent development as straightforward an experience as possible, similar to web development using popular web frameworks.

AEAs achieve their goals with the help of a search & discovery service for AEAs -- the <a href="oef-ledger">simple Open Economic Framework (sOEF)</a> -- a decentralized agent communication system -- the <a href="acn">Agent Communication Network (ACN)</a> -- and using <a href="oef-ledger">Fetch.ai's blockchain</a> as a financial settlement and commitment layer. AEAs can also be integrated with third-party blockchains, such as <a href="https://ethereum.org/en/" target="_blank">Ethereum</a>.


## Why build with the AEA Framework?

The AEA framework provides the developer with a number of features, which combined cannot be found anywhere else:

* The peer-to-peer <a href="acn">agent communication network (ACN)</a> allows your AEAs to interact with all other AEAs over the public internet.
* The search and discovery system <a href="simple-oef">sOEF</a> allows your AEAs to find other AEAs.
* The <a href="https://aea-registry.fetch.ai/" target="_blank">AEA registry</a> enables code sharing and re-use by providing a space in which AEAs or their individual components may be shared.
* The framework's <a href="ledger-integration">crypto and ledger APIs</a> make it possible for AEAs to interact with blockchains.
* The <a href="contract">contract</a> packages enable AEAs to interact with smart contracts in Fetch.ai and other third-party decentralised ledgers. 


## Next steps

To get started developing your own AEA, check out the <a href="quickstart">getting started</a> section.

To learn more about some of the distinctive characteristics of agent-oriented development, check out the guide on <a href="agent-oriented-development">agent-oriented development</a>.

If you would like to develop an AEA in a language different to Python then check out our <a href="language-agnostic-definition">language agnostic AEA definition</a>.

If you want to run a demo, check out the <a href="demos">demo guides</a>.


## Help us improve

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This developer documentation is a work in progress. If you spot any errors please open an issue on <a href="https://github.com/fetchai/agents-aea" target="_blank">Github</a> or contact us in the <a href="https://discord.com/invite/btedfjPJTj" target="_blank">developer Discord channel</a>.</p>
</div>

<br />
