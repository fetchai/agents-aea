<a name="aea.helpers.acn.agent_record"></a>
# aea.helpers.acn.agent`_`record

This module contains types and helpers for ACN Proof-of-Representation.

<a name="aea.helpers.acn.agent_record.AgentRecord"></a>
## AgentRecord Objects

```python
class AgentRecord()
```

Agent Proof-of-Representation to representative.

<a name="aea.helpers.acn.agent_record.AgentRecord.__init__"></a>
#### `__`init`__`

```python
 | __init__(address: str, representative_public_key: str, identifier: SimpleIdOrStr, ledger_id: SimpleIdOrStr, not_before: str, not_after: str, message_format: str, signature: str) -> None
```

Initialize the AgentRecord

**Arguments**:

- `address`: agent address
- `representative_public_key`: representative's public key
- `identifier`: certificate identifier.
- `ledger_id`: ledger identifier the request is referring to.
- `not_before`: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
- `not_after`: specify the lower bound for certificate validity. If it is a string, it must follow the format: 'YYYY-MM-DD'. It will be interpreted as timezone UTC-0.
- `message_format`: message format used for signing
- `signature`: proof-of-representation of this AgentRecord

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

<a name="aea.helpers.acn.agent_record.AgentRecord.identifier"></a>
#### identifier

```python
 | @property
 | identifier() -> SimpleIdOrStr
```

Get the identifier.

<a name="aea.helpers.acn.agent_record.AgentRecord.ledger_id"></a>
#### ledger`_`id

```python
 | @property
 | ledger_id() -> SimpleIdOrStr
```

Get ledger id.

<a name="aea.helpers.acn.agent_record.AgentRecord.not_before"></a>
#### not`_`before

```python
 | @property
 | not_before() -> str
```

Get the not_before field.

<a name="aea.helpers.acn.agent_record.AgentRecord.not_after"></a>
#### not`_`after

```python
 | @property
 | not_after() -> str
```

Get the not_after field.

<a name="aea.helpers.acn.agent_record.AgentRecord.message_format"></a>
#### message`_`format

```python
 | @property
 | message_format() -> str
```

Get the message format.

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

