<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.transaction`_`instruction

This module contains the TransactionInstruction of the solana module.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction.TransactionInstruction"></a>

## TransactionInstruction Objects

```python
class TransactionInstruction(NamedTuple)
```

Transaction Instruction class.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction.TransactionInstruction.keys"></a>

#### keys

Public keys to include in this transaction Boolean represents whether this
pubkey needs to sign the transaction.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction.TransactionInstruction.program_id"></a>

#### program`_`id

Program Id to execute.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction.TransactionInstruction.data"></a>

#### data

Program input.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction.TransactionInstruction.from_solders"></a>

#### from`_`solders

```python
@classmethod
def from_solders(cls,
                 ixn: instruction.Instruction) -> "TransactionInstruction"
```

Convert from a `solders` instruction.

:param ixn: The `solders` instruction.
:param The `solana-py` instruction.
:return: The `solders` instruction.


<a id="plugins.aea-ledger-solana.aea_ledger_solana.transaction_instruction.TransactionInstruction.to_solders"></a>

#### to`_`solders

```python
def to_solders() -> instruction.Instruction
```

Convert to a `solders` instruction.

**Returns**:

The `solders` instruction.

