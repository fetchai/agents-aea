The `DecisionMaker` can be thought off like a wallet manager plus "economic brain" of the AEA. It is responsible for the AEA's crypto-economic security and goal management, and it contains the preference and ownership representation of the AEA.

## Interaction with skills

Skills communicate with the decision maker via `InternalMessages`. There exist two types of these: `TransactionMessage` and `StateUpdateMessage`.

The `StateUpdateMessage` is used to initialize the decision maker with preferences and ownership states. It can also be used to update the ownership states in the decision maker if the settlement of transaction takes place off chain.

The `TransactionMessage` is used by skills to propose a transaction to the decision-maker. It can be used either for settling the transaction on-chain or to sign a transaction to be used within a negotiation.

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

The framework implements a default `DecisionMaker`. You can implement your own and mount it. The easiest way to do this is to run the following command to scaffold a custom `DecisionMakerHandler`:

``` bash
aea scaffold decision-maker-handler
```

You can then implement your own custom logic to process `InternalMessages` and interact with the `Wallet`. 

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For examples how to use these concepts have a look at the `tac_` skills. These functionalities are experimental and subject to change.
</p>
</div>