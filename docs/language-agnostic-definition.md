An Autonomous Economic Agent is, in technical terms, defined by the following characteristics:

- It MUST be capable of receiving and sending `Envelopes` which satisfy the following protobuf schema:

``` proto
syntax = "proto3";

package fetch.aea;

message Envelope{
    string to = 1;
    string sender = 2;
    string protocol_id = 3;
    bytes message = 4;
    string uri = 5;
}
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Additional constraints on envelope fields will be added soon!</p>
</div>

- It MUST implement each protocol with the required meta-fields:

``` proto

    // Meta fields
    int32 message_id = 1;
    string dialogue_starter_reference = 2;
    string dialogue_responder_reference = 3;
    int32 target = 4;
    oneof performative{
        ...
    }
```
 where `...` is replaced with the protocol specific performatives.

- It MUST implement protocols according to their specification.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This section is incomplete, and will be updated soon!</p>
</div>

- It SHOULD implement the `fetchai/default:0.1.0` protocol which satisfies the following protobuf schema:

``` proto
syntax = "proto3";

package fetch.aea.Default;

message DefaultMessage{

    // Custom Types
    message ErrorCode{
        enum ErrorCodeEnum {
            UNSUPPORTED_PROTOCOL = 0;
            DECODING_ERROR = 1;
            INVALID_MESSAGE = 2;
            UNSUPPORTED_SKILL = 3;
            INVALID_DIALOGUE = 4;
          }
        ErrorCodeEnum error_code = 1;
    }


    // Performatives and contents
    message Bytes_Performative{
        bytes content = 1;
    }

    message Error_Performative{
        ErrorCode error_code = 1;
        string error_msg = 2;
        map<string, bytes> error_data = 3;
    }


    // Standard DefaultMessage fields
    int32 message_id = 1;
    string dialogue_starter_reference = 2;
    string dialogue_responder_reference = 3;
    int32 target = 4;
    oneof performative{
        Bytes_Performative bytes = 5;
        Error_Performative error = 6;
    }
}
```

- It MUST process `Envelopes` asynchronously.

- It MUST have an identity in the form of, at a minimum, an address derived from a public key and its associated private key.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>Additional constraints will be added soon!</p>
</div>
