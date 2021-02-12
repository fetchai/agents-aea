<a name="aea.helpers.acn.agent_record"></a>
# aea.helpers.acn.agent`_`record

This module contains types and helpers for acn Proof-of-Representation.

<a name="aea.helpers.acn.agent_record.AgentRecord"></a>
## AgentRecord Objects

```python
class AgentRecord()
```

Agent Proof-of-Representation to representative.

<a name="aea.helpers.acn.agent_record.AgentRecord.__init__"></a>
#### `__`init`__`

```python
 | __init__(address: str, representative_public_key: str, message: bytes, signature: str, ledger_id: str) -> None
```

Initialize the AgentRecord

**Arguments**:

- `address`: agent address
- `representative_public_key`: representative's public key
- `message`: message to be signed as proof-of-represenation of this AgentRecord
- `signature`: proof-of-representation of this AgentRecord
- `ledger_id`: ledger id

<a name="aea.helpers.acn.agent_record.AgentRecord.address"></a>
#### address

```python
 | @property
 | address() -> str
```

Get agent address

<a name="aea.helpers.acn.agent_record.AgentRecord.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Get agent public key

<a name="aea.helpers.acn.agent_record.AgentRecord.representative_public_key"></a>
#### representative`_`public`_`key

```python
 | @property
 | representative_public_key() -> str
```

Get agent representative's public key

<a name="aea.helpers.acn.agent_record.AgentRecord.signature"></a>
#### signature

```python
 | @property
 | signature() -> str
```

Get record signature

<a name="aea.helpers.acn.agent_record.AgentRecord.message"></a>
#### message

```python
 | @property
 | message() -> bytes
```

Get the message.

<a name="aea.helpers.acn.agent_record.AgentRecord.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> str
```

Get ledger id.

<a name="aea.helpers.acn.agent_record.AgentRecord.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.helpers.acn.agent_record.AgentRecord.from_cert_request"></a>
#### from`_`cert`_`request

```python
 | @classmethod
 | from_cert_request(cls, cert_request: CertRequest, address: str, representative_public_key: str, data_dir: Optional[PathLike] = None) -> "AgentRecord"
```

Get agent record from cert request.

