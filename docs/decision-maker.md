The <a href="../api/decision_maker/base#decisionmaker-objects">`DecisionMaker`</a> can be thought of like a wallet manager plus "economic brain" of the AEA. It is responsible for the AEA's crypto-economic security and goal management, and it contains the preference and ownership representation of the AEA. The decision maker is the only component which has access to the wallet's private keys.

## Interaction with skills

Skills communicate with the decision maker via <a href="../api/protocols/base#message-objects">`Messages`</a>. At present, the decision maker processes messages of two protocols:

- <a href="../api/protocols/signing/message#signingmessage-objects">`SigningMessage`</a>: it is used by skills to propose a transaction to the decision-maker for signing.

- <a href="../api/protocols/state_update/message#stateupdatemessage-objects">`StateUpdateMessage`</a>: it is used to initialize the decision maker with preferences and ownership states. It can also be used to update the ownership states in the decision maker if the settlement of transaction takes place.

A message, say `msg`, is sent to the decision maker like so from any skill:
```
self.context.decision_maker_message_queue.put_nowait(msg)
```

The decision maker processes messages and can accept or reject them.

To process `Messages` from the decision maker in a given skill you need to create a `Handler`, in particular a `SigningHandler` like so:

``` python
class SigningHandler(Handler):

	protocol_id = SigningMessage.protocol_id

	def handle(self, message: Message):
		"""
		Handle a signing message.

		:param message: the signing message from the decision maker.
		"""
		# code to handle the message
```

## Custom `DecisionMaker`

The framework implements a default <a href="../api/decision_maker/default#decisionmakerhandler-objects">`DecisionMakerHandler`</a> and an advanced <a href="../api/decision_maker/gop#decisionmakerhandler-objects">`DecisionMakerHandler`</a>. You can also implement your own and mount it.

No further configuration is needed to use the default. To use the advanced decision maker handler, add the following configuration to the `aea-config.yaml` of your AEA (on page 1):

``` yaml
decision_maker_handler:
  config: {}
  dotted_path: "aea.decision_maker.gop:DecisionMakerHandler"
  file_path: null
```

The easiest way to add a custom decision maker handler is to run the following command to scaffold a custom `DecisionMakerHandler`:

``` bash
aea scaffold decision-maker-handler
```

You can then implement your own custom logic to process messages and interact with the `Wallet`. 

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For examples how to use these concepts have a look at the <code>tac_</code> skills. These functionalities are experimental and subject to change.
</p>
</div>