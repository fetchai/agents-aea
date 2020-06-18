The <a href="../api/decision_maker/base#decisionmaker-objects">`DecisionMaker`</a> can be thought of like a wallet manager plus "economic brain" of the AEA. It is responsible for the AEA's crypto-economic security and goal management, and it contains the preference and ownership representation of the AEA. The decision maker is the only component which has access to the wallet's private keys.

## Interaction with skills

Skills communicate with the decision maker via <a href="../api/decision_maker/messages/base#internalmessage-objects">`InternalMessages`</a>. There exist two types of these:

- <a href="../api/decision_maker/messages/transaction#transactionmessage-objects">`TransactionMessage`</a>: it is used by skills to propose a transaction to the decision-maker. It can be used either for settling the transaction on-chain or to sign a transaction to be used within a negotiation.

- <a href="../api/decision_maker/messages/state_update#stateupdatemessage-objects">`StateUpdateMessage`</a>: it is used to initialize the decision maker with preferences and ownership states. It can also be used to update the ownership states in the decision maker if the settlement of transaction takes place off chain.

An `InternalMessage`, say `tx_msg` is sent to the decision maker like so from any skill:
```
self.context.decision_maker_message_queue.put_nowait(tx_msg)
```

The decision maker processes messages and can accept or reject them.

To process `InternalMessages` from the decision maker in a given skill you need to create a `TransactionHandler` like so:

``` python
class TransactionHandler(Handler):

	protocol_id = InternalMessage.protocol_id

	def handle(self, message: Message):
		"""
		Handle an internal message.

		:param message: the internal message from the decision maker.
		"""
		# code to handle the message
```

## Custom DecisionMaker

The framework implements a default <a href="../api/decision_maker/default#decisionmakerhandler-objects">`DecisionMakerHandler`</a>. You can implement your own and mount it. The easiest way to do this is to run the following command to scaffold a custom `DecisionMakerHandler`:

``` bash
aea scaffold decision-maker-handler
```

You can then implement your own custom logic to process `InternalMessages` and interact with the `Wallet`. 

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For examples how to use these concepts have a look at the `tac_` skills. These functionalities are experimental and subject to change.
</p>
</div>